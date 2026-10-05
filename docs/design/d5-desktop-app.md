# D5 · Desktop app: build, install and launch — design

**TASK-10** · System Designer · task branch `v1-desktop` in
[deep-reasoning](https://github.com/michaeltheologitis/deep-reasoning), cut from `main` (v1 and v2 were written on
`design/d5` and merged; v3 on `design/d5-v3`, cut from `v1-desktop` at `3e9cee9`, changes only this file) · against
the approved spec [TASK-1](https://app.notion.com/p/3ed62fb22237814ab425c81b3844f012) (D5 in
full, §2, C3, §4's E10, E12 and testing layers, the dated notes at its end through "Scope additions approved,
2026-10-03").

**Pinned against (v2): merged.**
- **deep-reasoning `main` at `1f9fe52`**: D1 (#1–#8), the interim stop-test fix (#10), D2 (#11–#18) and D3
  (#19–#26). Every deep-reasoning `file:line` below is from it. Their documents: D1's design v5 `a2632a2` and
  as-built `f7a91f3` (`v1-dr-acp`); D2's design v3 `0f16c67` (`v1-library-store`) and as-built r2 `9ccacd4`
  (`as-built/d2-r2`); D3's design v9 `acde27b` (`v1-decompositions-panel`) and as-built r4 `e60ac65`
  (`as-built/d3-r2`).
- **Canvas fork `deep-reasoning` at `7c12afb`**: upstream `1ff45c2`, the ASE commit, the fork-only
  `launcher-live.yml` (`ba4d883`) and C3's stack (#5–#11). Every Canvas `file:line` below is from it. C3's design
  v3 `873aa92` on `design/c3` (its §4 is D5's contract) and as-built r2 `8c8b8c6`.
- **SDK fork `deep-reasoning` at `34c540c`**: upstream `53a4bc5`, the ASE and fork-CI commits, S2 (#3–#9), a test
  fix (#17), S1 (#10–#16) and the fork-only `dr-release.yml` (#18). Every SDK `file:line` below is from it. S1's
  design v2.3 `4725ccc` and as-built r4 `18da6e1` (`design/s1`); S2's design v2.5 and as-built r5 (`design/s2`,
  `48e6baa`).
- deep_reasoner_beta `d7334ae` · uv 0.8.17 for v1's measurements, 0.12.23 as the build pins it (§4.2.1).

**Expected (not merged; the skeleton's pins and D5's final part wait on these):**
- **`dr-2`**, the SDK fork's tag, which Michael pushes at `34c540c`; `dr-release.yml` then publishes the TypeScript
  client tarball as release `dr-2`. The existing `dr-1` (`cef3b24`) was cut from `dr/integration` and is not on
  `deep-reasoning`.
- **The redone wiring** (§8.6) on the Canvas fork's `deep-reasoning`, in place of `wiring/dr-1` (`9881d24`, built on
  C3's pre-refactor head `22272d9` and pinning `dr-1`), and after it the Canvas fork's first tag.
- **C1**, Canvas fork PR #4 (`feat/acp-subagent-sessions`, `4db661f`, being refactored; design v3 `8772b90`,
  as-built `d16d3df`).
- **C2**, Canvas fork PR #3 (`feat/agent-surfaces`, `a1ec3d1`, ready to split; design v2 `6e489ea`, as-built r2
  `fbf4230`).
- **D4**, `v1-custom-tools` (`461c3b5`; design v5 `60f1d00`), being split onto `main`.

*(v3: all of it landed. `dr-2` is on the SDK fork's `34c540c`, with its release's tarball. The redone wiring merged
into the Canvas fork's `deep-reasoning` as its #12 and was tagged `dr-1` (`fc87687`); C1 merged as Canvas #13–#19 and
C2 as #20–#26, with a toast fix (#27), tagged `dr-2` (`9d050ab`); two fork-only fixes for our build, #28 (no telemetry
prompt where a build cannot report) and #29 (onboarding keeps the active profile), tagged `dr-3` (`4355a36`), which
the build pins. D4 merged into `main` as #27–#33 (`53c821b`), and `v1-desktop` merged `main` at `53c821b`, `b2a74e0`
and `f1ca641`. §3.1 B1.)*

**Matches the build at `3e9cee9`** (v3): the head of `v1-desktop`. `main` (`f1ca641`) is its ancestor, so `git diff
f1ca641 3e9cee9` is D5 alone: 48 commits of code and tests besides v1's and v2's, 7,689 lines added and 134 removed in
63 files, this file aside. Since v2's `9ee36f6`: the skeleton and the final part, built in one pass; the four fixes
Michael approved at Gate B, and two more after the as-built r2; the Scout's five findings, adopted; and the literate
refactor (`d9b35f4` … `3e9cee9`). §3.1 B1–B29 give each change its commit, its reason and the test that pins it, and
the sections they name carry a v3 note in place. Line numbers in v3 notes are `3e9cee9`'s. v2's stay as v2 cited them:
deep-reasoning's `1f9fe52`; the Canvas fork's `7c12afb`, whose cited files are unchanged at the pin `4355a36` but for
`src/services/telemetry.ts` (§9); the SDK fork's `34c540c`, still the pin.

**In Gate C** (v3, 2026-10-05). Michael approved D5's behaviour at Gate B after running the `3c923aa` build in a macOS
26 VM ("It runs good btw generally."), and his rulings since v2 are §3.1 B4 and B13–B21: the four fixes
the as-built r1 proposed; Intel Macs dropped; deep-reasoning and its release downloads public; **the GitHub sign-in
kept in every build and release**, so deep_reasoner never ships inside the app (lifting it is TASK-45, only on his
word); his UI requests moved to a later UX round (TASK-42, 43, 44 and 46, and TASK-50 since), not into D5; and a
provider's error that reports no usage costs nothing against the cap. The stack is nine pull requests, #36 to #44,
each one commit on the one below and #36 on `main` at `f1ca641`. The top's tree (#44, `9455452`) is `3e9cee9`'s less
this file, and no branch of the stack carries a design or an as-built file. What to read beside each pull request is
the table "Which PR holds what" (§"Gate C: reading beside the PRs", below; #44's description carries the same table),
which cites v3 and the as-built document's revision 3 (`as_built/d5-desktop-app.md` on `as-built/d5`, `ffa34b1`, the
code at `3e9cee9`; r1's numbers kept, §8 the refactor). What changed since Gate B is §3.1 B18–B29: the fixes, then the
Scout's findings and the refactor. One approved behaviour moved on an error path, **B23** (as-built §6 #11): an
offline launch with no current runtime now fails naming `git fetch`, exit 11, not `no_access_dr`, exit 10. The tests
that carry each property are "Which tests carry which property", current at the stack top. The evidence at `3e9cee9`:
`ci.yml` [run 37256037218](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256037218), green,
**858 passed**, 115 deselected; `cross-repo.yml` [run
37256036928](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256036928), all four jobs green (E12
**17 of 17**, `bridge-replay` 12, `canvas-replay` 10 of 10); `desktop-release.yml` [run
37256038987](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256038987), `linux` and `macos`
green, the macOS launch smoke 2 of 2; and the live tier, `fork-live.yml` with `sdk_ref` `dr-2`, [run
37256842683](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256842683), S1 2 of 2 and S2 8 of 8
on gpt-6-luna through the key proxy. Each level of the stack has its own green `ci.yml` run; D5's own `cross-repo.yml`
ran on #42 (all four jobs green on attempt 1) and #44 (green on attempt 2: `canvas-replay` failed attempt 1 on
`exhausted.native.jsonl`, TASK-41's race, and passed 10 of 10 alone).

**Revisions** (newest first; each line says which sentences to stop trusting):
- 2026-10-05 · v3 · brought in line with the build at `3e9cee9`, the head of `v1-desktop`, whose tree less this file
  is the stack top's (#44, `9455452`), for Gate C; read beside the as-built r3 (`ffa34b1`). Since v2: both parts built
  in one pass; Michael's Gate B approval and rulings, the four fixes, and two more after r2; the Scout's five
  findings; the literate refactor. B-numbers are §3.1's. Stop trusting: the header's "Expected" list (landed, B1); §1
  item 1's universal `.dmg` (B14); §1.2 as a plan still to run (B1); decision C, §3 item 4, `runtime.lock.txt`,
  `RuntimeSpec`, §4.2.2 check 7, §4.4 steps 3–5, §4.4.2's order and its URL "parsed from `runtime.lock.txt`", and
  §4.4.3's `uv pip sync` and the paragraph under it (B22, B23, B2); decision M's and §7.5's `nightly.yml`, `has-d5`
  and trigger files (B26, B11); a private deep-reasoning and private releases in §2.2 and §3 items 1 and 2, §4.3.1's
  fetch line, and §7.5's `insteadOf` for deep-reasoning (B15); §4.2.1's placeholders (B1); §4.2.2's blobless fetch for
  check 8, check 2 as one sentence and check 5's "all of `setup`" (B24); §4.2.4's `ELECTRON_ARCH=universal`, its
  universal macOS build and its wrapper "whole" without the `mac` line (B14, B19); §4.3.2's exit codes (B6, B21, B27);
  §4.4.1's three rules (B3); §4.5.1 step 4's listing (B25); §4.7.3's "no usage reported: the reservation stands" (B4),
  and its silence on a body it cannot read (B5); in §5, `STATE_DIRNAME` and `state_dir`, `dr_app.runtime`'s
  `SetupError`, `LOCK_RESOURCE`, `RuntimeSpec`, `check_git(run=)`, `check_readable(url, run=)`, `runtime_is_current(…,
  spec)` and `install_runtime(layout, spec, …)`, `dr_app.cli`'s exit constants, the proxy's `DEFAULT_SPEND_CAP_USD`,
  its frozen `Spend(session, cap_usd, …)` and its `MappingProxyType` tables, and `Target` (B22, B27, B28, B14); §6's
  tables as complete (B6); §7.1–§7.3's names where their v3 notes rename them; §7.5's E12 as seven steps and a final
  flow, and `e12/main.yaml` (B7); §7.6's universal build and private release (B14, B15); §8's asks as open (all met);
  §9's W1, C1, C2 and D4 as expected, L6 as unverified, and U1's uv commands; §10's estimate; §11's items 1, 2, 4–6,
  8, 10–13 and 15–17 as open. Added without changing earlier sentences: the "Matches the build" and "In Gate C"
  paragraphs; §"Gate C: reading beside the PRs", with "Which PR holds what" and "Which tests carry which property";
  §3.1, B1 to B29 with "Size" and "The stack"; §6's new rows and the build's sentences; §11 items 19 to 22; and v3
  notes in §1, §1.1 (decisions A to F, I, K to N, P), §1.2, §1.3, §2.1 to §2.3, §3 items 1, 2, 4 and 13 to 15, §4.1 to
  §4.9, §6 to §11. Rewritten to the code: §5's blocks (each changed line marked `# v3:`), §4.2.4's wrapper and
  §4.3.1's bootstrap, each equal to its file at `3e9cee9`. No section is renumbered: §3.1 is new, and §3's items keep
  their numbers, so "§3 item N" still resolves.
- 2026-10-04 · v2 · brought up to date with what merged since v1's pins, so an Implementer can build the skeleton
  now; the changes, each with its source, are listed next. Stop trusting: v1's pins; §1.2 (rewritten: the Library
  App, E5's bridge replay and the macOS smoke join the skeleton, and it has a build order); decision M and every
  `self-hosted-v1` (now `main`); decision N's "or setup's fallback" and all of §4.9's fallback
  (`ensure_ingress_config`, before-start step 7, its test, its size); §4.5.1 step 3's 422 fallback,
  `SUBAGENTS_UNSUPPORTED` and `desired_profile`'s `subagents`; `AGENT_SERVER_SECRETS` (§4.7.2, §5.7); §6's `{…}`
  templates (a sentence with fields is now a function); §7.4's YAML (the file is on `main`, and has run); §7.5's
  probe App and `unshare -rn`; §8.2, §8.3 and §8.5 as asks (each is met); §9's line numbers at `02b7ac7` and
  `91430aa`, and its row A6; §10; §11 items 1, 2, 8 and 11. Added: decisions O and P; pin check 8 (§4.2.2);
  `run_logged` (§5.2); §8.7 (D4); §11 items 13 to 18.
- 2026-10-02 · v1 · first full-depth version. Folded in before it: Michael's rulings that the SDK fork is pinned
  by full commit (the tag named in a comment) and that D2's departures stand (a Library on a network filesystem
  is refused; the starter Library is gpt-6-luna on OpenAI); S1's opt-in `acp_subagents`; GitHub's rule that an
  on-demand workflow's file must exist on the default branch and a scheduled one runs only from it; C2's finding
  (C2 `72aa49f` §11) that App backends answer only on a separately configured ingress origin, which no launcher
  sets (§4.9).

**Changed since v1** (v2; each with its source and the sections it touches):

1. **C3 is merged, and its v3 is the contract** (Canvas `7c12afb`; C3 v3 §4, §4.4, §4.6, B9's v3 note). The keys,
   the phases and their environment are as v1 read them. New: a phase ends when the command's stdout and stderr
   close, not when it exits; at a timeout or a quit the command's process group is signalled even after the
   command itself has exited, SIGKILL follows 3 s after SIGTERM, and the launcher gives up 1 s after that; a quit
   ends the launcher in about 4 s, a timeout stops the launch within the limit plus about 4 s; a child that left the
   group (`setsid`), or whose output is redirected, can survive. `SHARED_DEFAULTS` is now parsed once and passed in
   (D-13), which changes nothing for a build that edits the file; the `[defaults]` line lists its names sorted (B5).
   → decision P, §4.3, §4.4.3, §6's log, §7.5 step 6, §9 C3, §11 item 14.
2. **C3 built the App-backend ingress default** (#5, B2, `scripts/dev-safe.mjs:883–884`; Michael's scope addition
   of 2026-10-03): every launcher gives the agent-server `OH_APP_BACKEND_PUBLIC_URL=http://127.0.0.1:<its port>`.
   D5 sets nothing, and §4.9's fallback and §8.5's ask are gone. → decision N, §1, §3 item 16, §4.4 step 7, §4.9,
   §5.5, §7.2, §8.5, §10.
3. **C3's live test proved the offline relaunch on the uv the build bundles**: uv 0.12.22 and 0.12.23, for
   upstream's commit and, through `wiring/dr-1`, for the SDK fork's `cef3b24` (runs 37171406704, 37148193696). The
   build pins `uv_version = "0.12.23"`. The network cut is `unshare --map-root-user -n`, then `ip link set lo up`,
   after an AppArmor sysctl on Ubuntu 24.04 (C3 B3, §7.5). → §4.2.1, §7.5 step 6, §9 U1, §11 item 15.
4. **S1 is merged, with the opt-in on the agent profile** (SDK #13: `profiles/agent_profile.py:292`,
   `resolver.py:305`, `seed.py:58`; S1 §5.1 guarantee 8): §8.2's ask is met, so setup always writes
   `acp_subagents: true` and the flat fallback goes. The scripted agent's `--transcript` mode is merged (#16, S1
   §5.1 guarantee 9), so E5's bridge replay joins the skeleton. → §1.2, §4.5.1, §5.4, §6, §7.2, §7.5, §8.2.
5. **S2 is merged** (SDK #3–#9): conversation header panels in the manifest (#4), `darwin-*` App backends and
   loopback never proxied (#3). The Library App's install and the macOS launch smoke no longer wait on it. → §1.2,
   §4.6, §7.6.
6. **The SDK fork's release path** (#18, `.github/workflows/dr-release.yml`, fork-only): a pushed `dr-N` tag runs
   the client's tests, packs `clients/typescript` and creates prerelease `dr-N` with
   `openhands-typescript-client-<version>.tgz` (1.50.1 at `34c540c`), once; the asset is never replaced, since the
   Canvas fork's lockfile pins its hash. → the header, §4.2.1, §4.2.2 check 8, §8.6, §9 T1.
7. **D1 is merged** (D1 as-built §4.6): `ModelRoute`, `RouteGrant`, `worker_env` and `PriceTable` as v1 read them;
   `ALWAYS_REMOVED` already holds `OPENHANDS_AUTOMATION_API_KEY` (D1 B2), as one of four glob patterns; `Options`
   has D1's five fields; `FakeOpenAI` is `deep_reasoning.acp.testing.fake_model`. The tool-client half of §8.1 is
   still to build. D1's EXP-27: deep_reasoner's `claude_code.child_env` drops every `CLAUDE_CODE*` variable. → §2.1,
   §2.2, §4.7.2, §5.7, §7.1, §8.1, §11 item 3.
8. **D2 is merged** (#11–#18): `dr-acp` without `--config` reads the Library, `dr-library serve --port P --home DIR`,
   `export DIR --home DIR` and its sentence, `/health` and `NETWORK_FILESYSTEMS` are as v1 relied on. New to D5:
   D2's `Host` guard on every platform (D2 as-built §2 #1), which E12 is the first to run through the bridge. →
   §2.2, §9 D2, §11 item 11.
9. **D3 is merged** (#19–#26; D3 §8.4): the App package `deep_reasoning.canvas_app` ships in the wheel (a manifest
   without a `backend` block, `dist/index.js`, `panel.svg`, and `ui/`, which `dr-library serve` serves at `/ui/`).
   D3 accepted D5's four proposals and asks seven things: D5 stages three files, not `ui/`; the page restarts a dead
   backend by starting its prepared revision; the notice is `SAFETY`, or `SAFETY_NO_CAP` under `--no-key-proxy`;
   and D3's equality test assumed `SAFETY.format(cap=7)` (D3 B19). → decisions G and O, §1.2, §2.3, §4.6, §5.5, §6,
   §7.2, §7.5 step 5 (D3's frame replaces the probe App), §8.3.
10. **deep-reasoning integrates on `main`**: D1 to D3 merged there, and `fork-live.yml` is on `main` in full
    (`633a00d`) and has run (37147706623 on `ci/fork-live`: S1 2 of 2, S2 8 of 8, without the proxy). → decision M,
    §1.3, §3 item 14, §7.4, §7.5, §8.6, §11 item 8.
11. **C1's contract, expected** (C1 v3 §4.12, §6.4, §9.4, A.9; its branch since Gate B): `OH_ACP_REPLAY_TRANSCRIPTS`
    as D5 named it, the replay spec's path, SUB-011's test ids, `expandAllSubagents` and `readRenderedSubagentTree`,
    and a frontend-only "Show sub-agent costs" setting, off by default (`show-subagent-costs-switch` on
    `/settings/app`; `dfde47e`, `4db661f`). → §7.5's final flow, §8.4, §9.
12. **C2's contract, expected** (C2 v2 §3.2 B15): the CX-006 and ASC-005 test ids; App frames read the ingress from
    `/server_info`'s `app_backend_ingress_url`. → §7.5, §8.4.
13. **D4's asks, expected** (D4 v5 §5, §10.6, §11.4): E10 again with its `echo_server.py` bound; one exception to
    §2.1's first row; the profile's `mcp_server_refs: null`; an E12 step and a cross-repo forwarding test. → §2.1,
    §2.2, §7.1, §7.5, §8.7.
14. **Found while re-reading**: the proxy imports `httpx`, which today arrives only through deep_reasoner, so it
    becomes a direct dependency (§4.1); a pinned commit must be on its fork's `deep-reasoning`, which `dr-1` is not
    (§4.2.2 check 8); the bridge strips `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from `dr-acp`'s environment
    whenever `CLAUDE_CODE_OAUTH_TOKEN` is a secret (§2.2, §11 item 3); a forced App reinstall is refused while any
    App's backend runs (§4.6); E12 is Python, so it evaluates C1's two DOM reads rather than importing them (§7.5).

**Where this file lives, and why nothing trips over it.** `docs/design/d5-desktop-app.md`. The `design/d5`
branch holds only documents (no `pyproject.toml`, no test runner, no package). On `v1-desktop`, cut from `main`,
which carries D1's `pyproject.toml`, pytest collects `tests/` only, the wheel is built from `src/deep_reasoning`
(and the new `packages/dr-app` from its own `src/`), the sdist excludes `docs/`, and ruff excludes `docs` (D1
§8.5). No design document goes into either fork, or onto `main`. The PR split leaves it behind. *(v3: still so at
`3e9cee9`: ruff's `extend-exclude` holds `docs`, pytest's `testpaths` is `tests`, and no pull request of the stack
carries this file.)*

**Reading guide.** *(v3)* Gate C: the "In Gate C" paragraph above, then §"Gate C: reading beside the PRs" below (which
PR holds what, and which tests carry which property), then §3.1 for what the build changed since v2. Beside each pull
request, the design sections its row names; every one of them carries its v3 notes in place. Gate B (v2): §1 (what
D5 is, its decisions, the skeleton, its build order and the final part), §2 (what the app protects and what it does
not) and §3 (departures from the spec): about 20 minutes. The Implementer:
§1.2 first, then everything; §5 is the signature index, §6 every user-visible sentence, §7 the tests and workflows.
Whoever redoes the wiring: §8.6. C1's and C2's authors: §8.4. D3's: §8.3. D4's: §8.7. D1's next revision: §8.1.
The Conductor: §1.2, §8 and §11.

## Gate C: reading beside the PRs

*(v3; new. Nothing here renumbers a section: §1 to §11 are v2's, with v3 notes, and §3.1 is added.)*

Gate C reads the code: 6,512 reviewable lines, 2,589 of code and 3,923 of tests, and the README's 161 (§3.1 "Size"),
in nine pull requests. Read each with the design sections and the as-built sections its row names. Bottom-up, the
stack is the key proxy, the grant that puts it between the worker and every key, setup's two phases, the SDK fork's
pin with what is checked against it, the build, the CI that installs and drives the app, the release, and the README
(§3.1 "The stack" says why in that order).

### Which PR holds what

Reviewable lines are non-blank added lines against the level below, as #44's description and the review ledger count
them; `uv.lock` (+2 in #36, +11 in #38) is not counted. B-numbers are §3.1's; as-built numbers are r3's.

| # | PR (head) | What it holds | Lines (code + tests) | Read beside: design v3 | as-built r3 |
|---|---|---|---|---|---|
| 1 | [#36](https://github.com/michaeltheologitis/deep-reasoning/pull/36) The key proxy forwards a model call with the real key in place of its token, and stops a conversation's spend at its cap (`2646b89`) | `acp/proxy.py`'s `SpendLedger` and `KeyProxy`; the proxy's sentences in `acp/texts.py`; `httpx` as a dependency; the request half of `test_key_proxy.py` | 916 (511 + 405) | §1.1 H, I; §4.7.1; §4.7.3; §5.7 (`Spend`, `SpendLedger`, `KeyProxy`); §6 (the proxy's sentences); §7.1 (the proxy's units); §3.1 B4, B5, B28 | §1.1 #5, #6, #25 (`Spend`); §2.3; §3 (the key proxy's HTTP); §4.1 (a request); §8 (the proxy) |
| 2 | [#37](https://github.com/michaeltheologitis/deep-reasoning/pull/37) dr-acp's worker gets tokens, not keys, for the main client and each tool's own, and a conversation's spend stops at $5 by default (`d3b7f52`) | D1's tool-client seam (`catalog.py`, `route.py`, `supervisor.py`, `worker/protocol.py`, `worker/runner.py`); `ProxyRoute` and `loopback_proxy_env`; `dr-acp`'s `--no-key-proxy` and `--spend-cap-usd`; `FakeOpenAI`'s `Authorization`; the grant half of `test_key_proxy.py`; E10 | 788 (249 + 539) | §1.1 H, J; §2.1; §2.2; §4.7.1; §4.7.2; §5.7 (`ProxyRoute`, `Options`); §7.1; §8.1; §8.7; §3.1 B9, B28 | §1.1 #16, #25 (the default cap); §2.3; §3 (`dr-acp`'s options); §4.1 (a grant); §5.2 (E10) |
| 3 | [#38](https://github.com/michaeltheologitis/deep-reasoning/pull/38) dr-app installs deep-reasoning at a commit into a private data home on every launch, and dr-app home and export serve the user (`3bda1fd`) | `packages/dr-app`: `layout.py`, `runtime.py`, `cli.py`'s before-start, `home` and `export`; the uv workspace; ruff over `packages/`; D3's notice test | 1,443 (761 + 682) | §1.1 B, C (superseded: B22), D, E, O, P; §4.3.2; §4.4 to §4.4.3; §4.8.1; §4.8.2; §5.1; §5.2; §5.6; §6 (setup's sentences); §7.2; §3.1 B2, B3, B6, B12, B21, B22, **B23**, B27 | §1.1 #3, #4, #15, #20, #22, #23; §1.3 #2, #4; §2.2; §3 (`dr-app`, exit codes, on disk); §4.2 (before-start); §5.4; §5.5; §6 #11 |
| 4 | [#39](https://github.com/michaeltheologitis/deep-reasoning/pull/39) Once the agent-server is up, dr-app makes dr-acp its default agent, says when no model key is saved, and starts the Library App (`c871ac5`) | `agent_server.py`, `profile.py`, `canvas_app.py`, `cli.py`'s after-ready; `tests/app/fake_agent_server.py` | 890 (371 + 519) | §1.1 F, G; §4.5; §4.5.1; §4.6; §5.3; §5.4; §5.5; §6 (setup's after-ready sentences); §7.2; §3.1 B6, B25 | §1.1 #24; §3 (the profile; the Library App's manifest); §4.2 (after-ready) |
| 5 | [#40](https://github.com/michaeltheologitis/deep-reasoning/pull/40) The SDK fork is pinned at dr-2, and the Library App, D1's recordings and D4's forwarding are checked against that agent-server (`9ef441d`) | `pins.toml`'s `[sdk_fork]`; `tests/crossrepo/` (the agent-server harness, E5, D4's forwarding); the Library App's `crossrepo` test; the `crossrepo` marker | 356 (8 + 348) | §1.1 A; §4.2.1; §7.2 (`test_canvas_app.py`'s `crossrepo` test); §7.5 (E5); §8.7; §3.1 B1, B10, B11 | §1.1 #11; §2.5; §5.2 (E5, the Library App); §6 #12 |
| 6 | [#41](https://github.com/michaeltheologitis/deep-reasoning/pull/41) desktop/build.py builds the Linux and Apple silicon packages from the Canvas fork at its pin, once the pins are checked to belong together (`4ff631c`) | `desktop/`: `build.py`, the rest of `pins.toml`, `bootstrap.sh`, `electron-builder.dr.mjs`; `test_build.py`, `test_bootstrap.py`; ruff over `desktop/` | 863 (511 + 352) | §1.1 A, K, L; §4.2 (all of it); §4.3.1; §5.8; §6 (the build's and the bootstrap's sentences); §7.3; §3.1 B1, B6, B12, B14, B15, B19, B20, B24 | §1.1 #1, #2, #7, #14, #19; §1.3 #3, #6; §2.1; §3 (`build.py`, `defaults.json`); §5.2 (pins) |
| 7 | [#42](https://github.com/michaeltheologitis/deep-reasoning/pull/42) cross-repo.yml checks the pins and drives the installed Linux app end to end, on every pull request that moves a pin or the app and every night (`4703dc2`) | `cross-repo.yml`, D5's own; `nightly.yml` deleted; E12, `tests/desktop/app.py`, `test_app.py`, `e12/subagents.py`; the `desktop` marker | 1,107 (147 + 960) | §1.1 M; §1.2; §4.9; §7.5; §8.4; §3.1 B7, B10, B11, B26, B29 | §1.1 #10, #11, #12; §2.4; §4.3; §5.2 (E12, E6); §6 #4, #5, #7, #12 |
| 8 | [#43](https://github.com/michaeltheologitis/deep-reasoning/pull/43) desktop-release.yml builds the Linux packages and the Apple silicon .dmg, launches the macOS app once, and attaches them to a v* tag's release (`c9ee72f`) | `desktop-release.yml`, D5's own; `test_launch_smoke.py` | 82 (30 + 52) | §4.2.6; §7.6; §3.1 B8, B11, B14, B15 | §1.1 #1, #13; §1.3 #5; §5.2 (the launch smoke); §7 (macOS) |
| 9 | [#44](https://github.com/michaeltheologitis/deep-reasoning/pull/44) The README says what deep-reasoning is and how to install, run and remove the desktop app (`9455452`) | `README.md`; `test_readme.py`; `pyproject.toml`'s `readme` | 67 (1 + 66), and the README's 161 | §1.3; §2.2; §2.3; §3 item 12; §4.2.6; §4.8.3; §3.1 B15, B16, B18 | §1.1 #9, #18; §6 #8; §7 (the uninstall paths) |

Across the stack, read the as-built's §1 (the divergences), §5.1 (the runs at `3e9cee9`), §6 (the open items) and §7
(what could not be verified, first that nothing ran on a Mac but GitHub's runner); and §3.1 B23 here, the one approved
behaviour that moved.

### Which tests carry which property

Each test's name states the property it pins. Paths are from the repository's root; `::` precedes a test, `[…]` its
parameters; the pull request that holds each test is in parentheses. Current at the stack top (`9455452`, the tree of
`3e9cee9`). A test runs in the default suite (`ci.yml`, every push and pull request) unless it is marked `crossrepo`
or `desktop`: those run in `cross-repo.yml` (and the smoke in `desktop-release.yml`).

*Part 1 · the key proxy and the cap* (§2.1, §4.7; #36, #37)

| Property | Tests |
|---|---|
| **No provider key `dr-acp` holds, and none of the agent-server's secrets, reaches the worker's environment, a cell, a process it starts, the transcript, the run log or any file under the home** (§2.1 rows 1 and 2; E10 #1) | `tests/acp/test_e10_keys.py::test_provider_keys_and_agent_server_secrets_never_reach_the_worker_a_cell_the_transcript_or_the_run_log` (#37; Linux only, it reads `/proc`); `tests/acp/test_key_proxy.py::test_the_key_is_removed_from_the_worker_env_by_value_under_any_name` (#37), `::test_upstream_error_bodies_never_echo_the_key` (#36), `::test_the_proxy_never_logs_a_key_or_a_token` (#37); D1's `tests/acp/test_route.py::test_the_agent_servers_secrets_never_reach_the_worker` (on `main`); in the installed app, `tests/desktop/test_e12.py::test_a_conversation_in_the_window_runs_dr_acp_and_its_key_stays_out` (#42, `desktop`) |
| **The proxy swaps the token for the key and forwards the call, for the main client and for each tool with its own client; a client whose key `dr-acp` lacks is left as configured** (§4.7.2, §8.1) | `test_key_proxy.py::test_the_token_is_swapped_for_the_key_and_the_call_forwarded`, `::test_an_anthropic_route_swaps_the_x_api_key` (#36); `::test_a_tool_with_its_own_client_gets_its_own_overrides`, `::test_a_client_without_a_held_key_is_left_as_configured` (#37); D1's seam: `tests/acp/test_catalog.py::test_materialize_hands_the_worker_each_tools_own_client`, `tests/acp/test_runner.py::test_the_run_config_takes_the_namespace_and_every_clients_overrides`, `::test_a_start_without_tool_overrides_leaves_every_tool_as_configured`, `tests/acp/test_route.py::test_the_direct_route_overrides_nothing` (`tool_upstreams` ignored) (#37); `tests/acp/test_fake_model.py::test_embeds_every_input_alike_and_records_each_call_with_its_authorization` (#37), the record E10 #1 reads to see the real key on the main client's and the `rag` tool's calls |
| **A token is worth nothing outside its run; a route forwards only to its configured upstream, and only model calls** (§2.1 rows 4 and 5) | `test_key_proxy.py::test_a_wrong_or_missing_token_is_refused_and_nothing_is_forwarded`, `::test_a_released_runs_tokens_stop_working`, `::test_a_route_forwards_only_to_its_configured_upstream`, `::test_only_model_endpoints_are_forwarded[…]` (#36: POSTs to `files`, `fine_tuning/jobs`, `batches`, `images/generations` and `chat/completions/../../files`, and a GET on `chat/completions`) |
| **Spending through the proxy stops at the conversation's cap**: reserved before forwarding, settled after; an unpriced model refused off loopback; concurrent calls overshoot by at most their reservations; streams metered; the count survives a restart; a provider's error that reports no usage costs nothing (§2.1 row 3; decision I; B4) | `tests/acp/test_e10_keys.py::test_a_call_past_the_spend_cap_is_refused_and_never_forwarded` (#37, E10 #2: three prompts, one after `dr-acp` restarts); `test_key_proxy.py::test_an_unpriced_model_is_refused_unless_the_upstream_is_loopback`, `::test_concurrent_calls_overshoot_the_cap_by_at_most_their_reservations` (20 at once), `::test_a_streamed_openai_call_is_metered_from_its_last_chunk`, `::test_a_streamed_anthropic_call_is_metered_from_message_start_and_delta`, `::test_the_ledger_continues_after_a_restart`, `::test_provider_errors_release_their_reservations`, `::test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused` (#36) |
| **Loopback calls bypass a Mac's system proxies; every other call keeps them** (§4.7.2 step 5) | `test_key_proxy.py::test_loopback_calls_bypass_macos_system_proxies_and_others_keep_them` (#37; `system_proxies` faked, no Mac) |
| **The proxy is on by default with a $5 cap per conversation; `--no-key-proxy` keeps D1's direct route** (decision J) | `test_key_proxy.py::test_no_key_proxy_keeps_d1s_direct_route`; D1's `tests/acp/test_cli.py::test_options_default_to_native_a_minute_of_heartbeat_warnings_and_the_proxy` (#37) |
| **An MCP server gets a provider key only when its Canvas settings name it, and the worker's token never** (§2.1 row 1's exception; §8.7; B9) | `test_e10_keys.py::test_an_mcp_server_gets_a_provider_key_only_when_its_settings_name_it_and_the_worker_never_does[unnamed, named]` (#37) |
| **The proxy's sentences are §6's, verbatim** | `tests/acp/test_texts.py::test_the_key_proxys_sentences_are_d5s_verbatim` (#36) |
| **Through the proxy against a real provider** (the live tier) | not a D5 test: S1's two and S2's eight live tests, `fork-live.yml` with `dr-acp` from this branch (§7.4; run 37256842683) |

*Part 2 · setup's before-start* (§4.3, §4.4, §4.8; #38)

| Property | Tests |
|---|---|
| **The data home**: the root when it is local; `/var/tmp/deep-reasoning-<uid>` under a network home, refused when not a private folder of ours; a recorded home kept; never one too long for a Claude run's socket (§4.4.1; B3) | `tests/app/test_layout.py::test_the_default_home_is_the_root_when_it_is_local`, `::test_a_network_home_moves_the_data_to_var_tmp`, `::test_a_var_tmp_directory_not_ours_is_refused[link, other-owner, mode-0755]`, `::test_a_recorded_home_is_kept`, `::test_our_network_filesystems_are_d2s`, `::test_a_home_too_long_for_a_claude_runs_socket_is_refused[…]` (five homes, Linux and macOS, 86 to 130 bytes), `::test_setup_refuses_a_default_home_too_long_for_a_claude_runs_socket`, `::test_linuxs_limit_is_where_a_socket_stops_binding[107, 108]` |
| **A first launch checks, then installs exactly the commit's own lock into a relocatable venv; a failed check installs nothing** (§4.4.2, §4.4.3; B2, B22, B23) | `tests/app/test_runtime.py::test_a_first_launch_checks_then_installs_the_commits_own_lock`, `::test_deep_reasoners_pin_is_read_from_uv_lock_as_pyproject_names_it`, `::test_the_runtimes_uv_sync_reads_no_project_setting_that_changes_its_set`, `::test_the_runtimes_commands_run_from_where_the_install_leaves_them`, `::test_an_unreadable_deep_reasoner_installs_nothing`, `::test_without_uv_nothing_is_installed`, `::test_the_runtime_lock_installs_on_every_platform_the_app_ships_for[x86_64-unknown-linux-gnu, aarch64-apple-darwin]` (reads PyPI, B12); `tests/app/test_cli.py::test_a_failed_check_exits_with_its_code_and_its_sentence` |
| **A relaunch with nothing changed installs nothing and needs no network; a change or a broken runtime reinstalls; a failed install keeps `current`** (decision E; §4.4.3) | `test_runtime.py::test_a_relaunch_with_nothing_changed_runs_no_uv_and_no_git`, `::test_a_new_commit_reinstalls`, `::test_a_broken_runtime_python_reinstalls`, `::test_a_failed_install_keeps_current_and_exits_11[git fetch, uv sync]`, `::test_an_interrupted_install_is_cleaned_up`; `test_cli.py::test_the_bin_links_lead_to_the_runtime`; in the installed app, `tests/desktop/test_e12.py::test_setup_relaunches_offline_from_its_cache_and_installs_nothing` (#42, `desktop`) |
| **Setup never prompts, never holds the launcher's phase, leaves nothing running, and never overlaps itself** (decision P; §4.3.2) | `test_runtime.py::test_git_never_prompts[None, ssh -i ~/.ssh/work]`, `::test_a_background_child_that_keeps_the_output_never_holds_setup`, `::test_nothing_setup_starts_leaves_the_process_group`; `test_cli.py::test_two_setups_never_run_at_once`; in the installed app, `test_e12.py::test_closing_the_window_quits_the_app_and_leaves_nothing_running` (#42, `desktop`) |
| **`setup.json` round-trips atomically, and one this app cannot use is explained, exit 14, not a traceback** (B21) | `test_layout.py::test_setup_state_round_trips_and_writes_atomically`, `::test_a_setup_state_this_app_could_not_have_written_says_why[seven files]`, `::test_a_setup_state_that_cannot_be_read_says_why`; `test_cli.py::test_a_setup_state_it_cannot_use_is_explained_and_exits_14[newer, no version, not JSON × setup, home]` |
| **`dr-app home` and `dr-app export` serve the user** (§4.8) | `test_cli.py::test_home_records_a_local_folder_and_refuses_a_network_one`, `::test_home_refuses_a_folder_too_long_for_a_claude_runs_socket`, `::test_export_runs_the_runtimes_dr_library_with_the_home` |
| **Setup's sentences are §6's, and D3's notice is D5's sentence** (decision O) | `tests/app/test_texts.py::test_sentences_with_fields_are_the_designs_verbatim` (#38, #39); D3's `tests/canvas_app/test_notice.py::test_the_notice_is_d5s_sentence_with_the_cap` (#38, `browser`, in `ci.yml`'s `canvas-app` job; it stops skipping here) |

*Part 3 · setup's after-ready* (§4.5, §4.6; #39, #40)

| Property | Tests |
|---|---|
| **Setup makes `deep_reasoner` the app's agent once, owns four fields and the `--home` pair, and keeps the rest the user's** (decision F; §4.5.1; B25) | `tests/app/test_profile.py::test_the_profile_is_created_and_made_the_default_once`, `::test_a_relaunch_writes_nothing` (one request), `::test_the_users_spend_cap_and_other_arguments_survive`, `::test_the_profile_always_turns_sub_agent_sessions_on`, `::test_a_refused_profile_fails_setup_with_exit_12`, `::test_a_deleted_profile_is_recreated_but_not_reactivated`, `::test_a_command_path_with_spaces_is_shell_quoted`; in the installed app, `test_e12.py::test_onboarding_keeps_deep_reasoner_and_starts_the_first_conversation_with_it` (#42, `desktop`) |
| **The phase comes from the launcher; a hand run does both; after-ready needs the launcher's variables; nothing secret is printed** (§4.3.2) | `test_cli.py::test_the_phase_comes_from_the_launchers_variable`, `::test_a_hand_run_does_both_phases_when_the_agent_server_is_up`, `::test_after_ready_without_the_agent_server_is_a_usage_error[AGENT_SERVER_URL, SESSION_API_KEY]`, `::test_nothing_secret_is_printed` |
| **The Library App is staged byte for byte the same, from D3's three files and one script, then installed, enabled once, approved and started; a refusal only warns** (decision G; §4.6) | `tests/app/test_canvas_app.py::test_the_backend_artifact_is_byte_for_byte_stable`, `::test_the_manifest_names_both_architectures_and_the_home[Linux, Darwin]`, `::test_only_the_apps_own_files_are_staged`, `::test_our_app_name_is_d3s`, `::test_a_first_install_enables_approves_and_starts`, `::test_a_relaunch_only_starts_the_backend`, `::test_an_upgrade_stops_reinstalls_and_reapproves`, `::test_a_disabled_app_is_left_alone`, `::test_an_unsupported_platform_says_so`, `::test_an_agent_server_refusal_warns_and_setup_succeeds` (#39) |
| **Against the pinned agent-server, the staged App passes `prepare` and its backend answers `/health`** | `test_canvas_app.py::test_the_staged_app_passes_prepare_and_its_backend_answers_health` (#40, `crossrepo`); on GitHub's macOS runner, `tests/desktop/test_launch_smoke.py::test_the_first_launch_starts_the_library_backend_and_the_app_quits` (#43); in the installed Linux app, `test_e12.py::test_the_first_launch_installs_everything_and_opens_the_window` (#42) |

*Part 4 · the build* (§4.2, §4.3.1; #41)

| Property | Tests |
|---|---|
| **The pins belong together, or the build names the two values that disagree** (§4.2.2's seven checks; B24) | `tests/desktop/test_build.py::test_pins_that_belong_together_pass_every_check`, `::test_pins_with_a_short_commit_are_refused`, `::test_a_tag_that_moved_is_refused`, `::test_a_canvas_fork_wired_to_another_sdk_commit_is_refused`, `::test_a_typescript_client_from_another_tag_is_refused`, `::test_a_different_acp_python_is_refused`, `::test_a_fork_that_carries_our_values_is_refused`, `::test_a_dirty_or_unpushed_checkout_is_refused`, `::test_a_commit_off_the_forks_deep_reasoning_branch_is_refused` (each with injected readers); against the real forks, `cross-repo.yml`'s `pins` job (#42) |
| **The build writes only D5's four keys, telemetry off, and a setup command that embeds the bootstrap and the commit** (§4.2.3; decision K) | `test_build.py::test_defaults_gain_only_d5s_four_keys`, `::test_telemetry_is_off_in_the_built_defaults`, `::test_the_setup_command_embeds_the_bootstrap_and_the_commit` |
| **Macs are Apple silicon only, from macOS 14, and each target builds only on its own machine** (B14, B19) | `test_build.py::test_the_mac_build_is_one_arm64_dmg_whose_binaries_are_arm64_only`, `::test_a_mac_build_that_is_not_arm64_only_is_refused[universal, intel, universal-binary]`, `::test_a_mac_app_that_opens_before_macos_14_is_refused[12.0, 13.0, None]`, `::test_a_target_builds_only_on_the_machine_it_is_for[…]` (each target on its own machine and on the other's), `::test_the_build_offers_no_universal_or_intel_mac_target`; on the built app, `test_launch_smoke.py::test_the_mac_app_and_the_runtime_it_ran_are_arm64_only` (#43) |
| **A package's payload is listed whole, so the `deep_reasoner` check sees every path** (§2.1 row 7) | `test_build.py::test_a_debs_payload_paths_keep_their_spaces` (skipped without `dpkg-deb`); the check itself runs in every build (`desktop-e2e`, `desktop-release.yml`), with no unit test of its refusal |
| **The committed pins load, and two tests restate them** (B12) | `test_build.py::test_the_committed_pins_load`, `::test_the_committed_sdk_pin_is_34c540c_tagged_dr_2`: a pin bump edits both |
| **The bootstrap explains the two failures before `dr-app` exists, and passes `dr-app`'s own exit codes on** (§4.3.1; B15) | `tests/app/test_bootstrap.py::test_no_git_says_how_to_install_it`, `::test_an_unreachable_deep_reasoning_says_so_and_keeps_uvx_status`, `::test_dr_apps_own_failure_passes_through_without_the_fetch_line`, `::test_the_arguments_reach_dr_app_unchanged` |

*Part 5 · across the repositories, and the installed app* (§7.5, §7.6; #40, #42, #43, #44)

| Property | Tests |
|---|---|
| **E5: each of D1's ten native recordings is stored by the pinned agent-server as the tree it records** | `tests/crossrepo/test_bridge_replay.py::test_each_native_recording_is_stored_as_the_tree_it_records[ten recordings]` (#40, `crossrepo`), with `::test_the_recorded_shape_places_every_child_under_its_cell` (default suite) |
| **D4's forwarding: an MCP server in the agent-server's settings reaches a cell through the profile and `dr-acp`, its secret with it** | `tests/crossrepo/test_mcp_forwarding.py::test_an_mcp_server_in_the_agent_servers_settings_reaches_a_cell_with_its_secret` (#40, `crossrepo`) |
| **E6: C1's replay spec renders each recording as stored** | not a D5 test: `cross-repo.yml`'s `canvas-replay` job runs C1's spec in the pinned Canvas (#42) |
| **E12, the installed Linux app on a fake model** (§7.5; B7): one launch, seventeen tests in file order | `tests/desktop/test_e12.py` (#42, `desktop`): the launch, `::test_the_first_launch_installs_everything_and_opens_the_window`; onboarding and consent, `::test_the_first_launch_asks_for_no_telemetry_consent`, `::test_onboarding_keeps_deep_reasoner_and_starts_the_first_conversation_with_it`, `::test_nothing_records_telemetry_consent_and_settings_offer_no_analytics_switch`; E10 inside the app, `::test_a_conversation_in_the_window_runs_dr_acp_and_its_key_stays_out`; the bridge in Electron's Chromium (§4.9), `::test_d3s_frame_works_through_the_bridge_in_electrons_chromium`; C1, `::test_sub_agents_nest_under_the_cells_that_spawned_them_as_the_run_log_records`, `::test_each_sub_agent_shows_its_latest_cost_once_the_setting_is_on`, `::test_stop_on_one_sub_agent_stops_it_and_its_branch`; C2 and D3, `::test_the_home_screen_offers_the_namespaces_and_each_ones_decompositions`, `::test_create_decomposition_in_the_header_panel_saves_into_the_conversations_namespace`, `::test_the_next_conversation_in_the_namespace_offers_the_decomposition_and_uses_it`, `::test_the_header_panel_keeps_working_past_its_first_backend_session`; D4, `::test_the_tools_tab_shows_the_safety_notice_with_d4s_risk_line_under_it`, `::test_an_mcp_server_granted_in_the_tools_tab_is_called_by_the_next_conversation`; then `::test_closing_the_window_quits_the_app_and_leaves_nothing_running` and `::test_setup_relaunches_offline_from_its_cache_and_installs_nothing` |
| **The launch harness says why a launch failed, and its fresh HOME stores no git credentials** (B8) | `tests/desktop/test_app.py::test_a_failed_wait_says_why_with_the_logs_last_lines[exited, reported-failure, timed-out]`, `::test_git_under_the_fresh_home_stores_no_credentials_whatever_the_systems_helper` (#42) |
| **The macOS app, as built, starts the Library backend, quits cleanly, and is arm64 only** (§7.6; B8, B14) | `tests/desktop/test_launch_smoke.py::test_the_first_launch_starts_the_library_backend_and_the_app_quits`, `::test_the_mac_app_and_the_runtime_it_ran_are_arm64_only` (#43, `desktop`, on `macos-latest`) |
| **The README names what the code does** (B18) | `tests/desktop/test_readme.py::test_the_mac_steps_name_the_package_and_the_app_the_build_produces`, `::test_the_key_is_the_one_setup_asks_for_where_setup_says`, `::test_the_access_check_is_the_one_setup_runs`, `::test_the_terminal_commands_are_the_ones_setup_links`, `::test_uninstall_removes_what_the_app_writes`, `::test_the_safety_section_quotes_setup_with_the_cap_setup_sets`, `::test_the_data_table_names_everything_setup_keeps_in_the_root`, `::test_dr_app_home_says_how_long_a_folder_may_be` (#44) |

**Not pinned by any test:** the GitHub readers of checks 4 and 8 (`read_file_at`, `is_on_branch`), which run only in
builds and the `pins` job, and whose HTTP errors other than check 8's 404 (a rate limit) end `build.py` in a traceback
(as-built §1.3 #6; §11 item 19); the proxy's `bad_body` refusal and its uncompressed path (B5; §11 item 20); the
build's refusal of a payload path holding `deep_reasoner` (the check runs in every build; no build has failed it); the
system-proxy export on a real Mac (unit-tested with `system_proxies` faked); the Claude CLI behind the proxy (§11 item
3); macOS 13 refusing to open the app (Apple's handling of `LSMinimumSystemVersion`, which `verify()` checks is
declared); onboarding's **Close** on **Say hello** without a key, which the README tells a user to press and E12 never
presses; the offline case of B23 as a user meets it (a failing `git fetch` stands for it in the tests); setup's
failure cases run through the bootstrap rather than `dr-app` alone (the bootstrap's tests stub `uvx`); the README's
Electron folders in uninstall; and TASK-38's cause.

---

## 1 · What D5 is

v1 is a desktop app (Q7 (b)). D5 turns the pinned forks and this repo into one download per OS, and makes the
app's own launcher install the rest, as the user, on first launch. It is four things:

1. **The build** (`desktop/`). It checks that the pins belong together, checks out the Canvas fork at its pinned
   commit, writes D5's values into that checkout's `config/defaults.json` (the state directory, the setup
   command, telemetry off), builds the frontend, and packages it with electron-builder under our product name.
   Output: one universal `.dmg`, an `.AppImage` and a `.deb`, unsigned as upstream's are. Neither fork gets a
   commit from D5: every change is made to a build checkout. *(v3: one Apple silicon `.dmg` for macOS 14 or later,
   built on an Apple silicon Mac, and the Linux packages on Linux x86-64: B14, B19.)*
2. **`dr-app`** (`packages/dr-app/`), the setup command C3's launcher runs as the user on every launch, before
   the stack starts and again once the agent-server answers. It installs deep-reasoning (and through it
   deep_reasoner) with the user's own git credentials into a private runtime, picks where the user's data lives,
   registers the `deep_reasoner` agent profile, and installs, approves and starts the Library App (D3's, which
   v1 left to the final part; v2: D3 and S2 are merged, so it is the skeleton's). On a launch where nothing changed
   it does almost nothing. It also offers `dr-app export` and `dr-app home`.
3. **The key proxy** (`src/deep_reasoning/acp/proxy.py`), inside `dr-acp`'s front process, implementing D1's
   `ModelRoute`. The worker gets a token instead of each provider key; the proxy swaps the key in, forwards only
   model calls, and refuses a call once the conversation's spend cap is reached.
4. **The cross-repo CI** (`.github/workflows/`): the shared live workflow for S1's and S2's live tiers with `dr-acp`
   behind the bridge (*v2:* built and on `main`, §7.4); E12 on the real Linux app, the golden replays into the pinned
   agent-server (E5) and Canvas (E6), and the pin checks, nightly and on every pin bump; the per-OS release build.
   *(v3: `cross-repo.yml` runs nightly on its own schedule once it is on `main`, and `nightly.yml` goes, B26; release
   downloads are public, B15.)*

*(v3: and the README, which v2 named only as "the README's install section": `README.md` at the root says what
deep-reasoning is, how to install, run and remove the app, and §2 in short, and `tests/desktop/test_readme.py` pins
its names and commands to the code's, B18.)*

A launch of the installed app, end to end:

```text
Deep Reasoning.app  (Canvas fork's Electron shell at its pinned commit; D5's defaults.json; product name)
  electron/main.mjs → dev-with-automation.mjs main()                                        (C3 §3.2)
    1 defaults.json fills: OH_AGENT_SERVER_GIT_REPO / _REF  (the wiring commit: the SDK fork's commit)
                           OH_CANVAS_SAFE_STATE_DIR = ~/.deep-reasoning/canvas/agent-canvas  (D5), key files in it
    2 setup before-start:  sh bootstrap.sh → uvx --from git+…/deep-reasoning@<commit>#subdirectory=packages/dr-app
                             dr-app setup:  data home · runtime ~/.deep-reasoning/runtime/current (from the lock)
                           the phase ends when the command's output closes (C3 v3 §4.2; decision P)
    3 agent-server         uvx, SDK fork at its commit; persistence root ~/.deep-reasoning/canvas;
                           App-backend ingress OH_APP_BACKEND_PUBLIC_URL = http://127.0.0.1:18000   (C3 B2, §4.9)
    4 setup after-ready:   the same command, with AGENT_SERVER_URL and SESSION_API_KEY
                             agent profile deep_reasoner · Library App dr-library installed, approved, started
    5 automation, static frontend, ingress → window on http://localhost:8000
         the Library panel's frame: http://127.0.0.1:18000/app-backends/dr-library/ui/…  (a separate origin and site;
         its button and panel are C2's, final part)

  a conversation → the agent-server's ACP bridge → ~/.deep-reasoning/runtime/current/bin/dr-acp
                                                       --home <DR_HOME> --spend-cap-usd 5
     dr-acp front ── key proxy, 127.0.0.1:<port>, its own thread ──(real key)──▶ the provider
          │                         ▲
          └─ worker (D1) ───────────┘ model calls carry a token, never the key; the env holds no key
```

Where everything lives on the user's machine:

| Path | What | Written by |
|---|---|---|
| `~/.deep-reasoning/` | the app's root, mode 0700 | `dr-app` |
| `~/.deep-reasoning/canvas/` | the agent-server's persistence root (C3 §4.3): `settings.json`, `secrets.json`, `agent-profiles/`, `canvas-extensions/`, `automation/` | the agent-server, automation |
| `~/.deep-reasoning/canvas/agent-canvas/` | C3's state directory: conversations, workspaces, `secret-key.txt`, `api-key.txt` | the launcher, the agent-server |
| `~/.deep-reasoning/runtime/<commit>/`, `runtime/current` → it | the venv holding `dr-acp`, `dr-library`, `dr-app`, deep_reasoner's `dr` | `dr-app` |
| `~/.deep-reasoning/bin/` | `dr-app` and `dr`, linked to `runtime/current/bin/` | `dr-app` |
| `~/.deep-reasoning/canvas-app/<digest>/` | the Library App package staged for this machine: D3's manifest with D5's `backend` block, `dist/index.js`, `panel.svg`, the backend artifact | `dr-app` |
| `~/.deep-reasoning/setup.json`, `setup.lock` | what setup last did; a lock while it runs | `dr-app` |
| **DR_HOME**: `~/.deep-reasoning` itself, or `/var/tmp/deep-reasoning-<uid>` on a network home | D1's and D2's home: `library.sqlite`, `sessions/`, `runs/`, `prices.yaml`; D5's `spend/` | D1, D2, D5 |

The names never collide: D1's and D2's entries (`library.sqlite`, `sessions/`, `runs/`, `prices.yaml`) and
D5's (`canvas/`, `runtime/`, `bin/`, `canvas-app/`, `setup.json`, `setup.lock`, `spend/`) are disjoint, so
DR_HOME can be the root itself. A terminal `dr-acp` or `dr-library` with no `--home` uses `~/.deep-reasoning`
(D1's default), so on a local home the terminal and the app share one Library.

*(v3)* In the launch above, step 2's runtime comes from the commit's own `uv.lock`, not a packaged export (B22). While
an install runs, `runtime/` also holds `<commit>.tmp-<pid>` (the venv being built) and `<commit>.tmp-<pid>-source`
(the commit's fetched tree); the next install removes either if a quit left it. The README's data table is this
table's, and a test holds them together (`test_the_data_table_names_everything_setup_keeps_in_the_root`).

### 1.1 Decisions this design takes

The spec's seven decisions in §2 stand; these are the next layer down.

| # | Decision | Why | Rejected |
|---|---|---|---|
| A | **Every pin is a full commit; tags are recorded beside them for people.** `desktop/pins.toml` holds each fork's repository, commit and tag; the build records deep-reasoning's own commit (its `HEAD`) in the setup command. *(v2: and each pinned commit must be on its fork's `deep-reasoning` branch, §4.2.2 check 8.)* *(v3: built so; check 8 asks GitHub's compare API, B24; the Canvas fork is pinned at `4355a36`, tag `dr-3`, B1.)* | Michael's ruling for the SDK fork; C3 §2.3 measured that uv reuses only a commit offline, and the same holds for D5's own `uvx` command (C3 §4.6). One rule for all three repos. *(v2: the spec pins each fork by a `dr-N` tag on its `deep-reasoning` branch, and the fork stacks merge there; `dr-1` was cut from `dr/integration`.)* | Tags in `defaults.json` (C3's tag-resolving variant, ≈170 lines; ruled out). |
| B | **The setup command is a ten-line `sh` bootstrap around `uvx` of a separate, standard-library-only package, `deep-reasoning-app`** (`packages/dr-app`), fetched by commit with `#subdirectory=`. *(v3: built so. deep-reasoning is public, so the bootstrap's second sentence asks only that the computer be online, B15.)* | Whatever `uvx` installs must be fetched before anything of ours can speak. If the setup command were the main package, `uvx` would first fetch deep_reasoner and fail with uv's words, before any check could say "ask Dean for access". The small package needs nothing private but deep-reasoning itself, and the bootstrap explains a missing `git` or an unreadable deep-reasoning, the two failures that happen before `dr-app` exists. A commit-pinned `uvx` of a package with no dependencies starts from uv's cache, offline included (C3 §2.3). | `uvx --from git+…/deep-reasoning@<commit> dr-app setup` as C3 §4.6 sketches (the private fetch fails before our checks, so the spec's failure messages cannot be ours). A setup script bundled into the app's resources (it would need a path into the bundle, which differs per launch for an AppImage, and a file added inside the fork's `uv` resource directory). |
| C | **`dr-app` installs a runtime venv from a committed export of `uv.lock`** (`runtime.lock.txt`, exact versions, platform markers kept), on uv's managed Python 3.12, into `runtime/<commit>/`, then swaps the `runtime/current` link atomically. *(v3: superseded by B22. The runtime is `uv sync --frozen --no-dev --no-editable --all-packages` of the commit's own tree, fetched with git into `runtime/`, into a relocatable venv (B2); there is no exported lock. The reason stands: users run the set CI tested, which the commit's `uv.lock` fixes.)* | Users run exactly the dependency set CI tested; a transitive release between our test and their first launch cannot break them. The link keeps every path that is written into a profile or an App stable across upgrades. A managed Python survives a system or Homebrew Python upgrade. | `uv tool install` (resolves afresh, ignoring the lock; writes into the user's global tool and `~/.local/bin` directories). The `uvx` environment itself (uv's cache can be pruned under it). |
| D | **One root, `~/.deep-reasoning`. The agent-server's persistence root is `~/.deep-reasoning/canvas`** (state directory `…/canvas/agent-canvas`). **DR_HOME is `~/.deep-reasoning`, or `/var/tmp/deep-reasoning-<uid>` when the home directory is on a network filesystem.** Every process is told the home with `--home`; DR_HOME is never set in any environment. *(v3: and never a home too long for a Claude run's socket, B3.)* | C3 §4.3: the state directory's parent holds everything the agent-server persists, so it must be ours, not `~/.openhands`. D2's ruling: the Library refuses a network filesystem, so setup picks local disk. deep_reasoner reads `DR_HOME` itself as the root of its Claude runs (`v2/claude_code.py:270`), so an exported DR_HOME would reach the worker with a second meaning. | `~/.openhands/deep-reasoning` (the spec's mock-up; shares settings, secrets, profiles and Apps with stock Agent Canvas, C3 §2.4). |
| E | **Setup is idempotent, and its cheap path is a JSON read, a few `stat`s and one exec of the runtime's Python**; it changes anything only when a pin, the data home or the App package changed, or something it installed is gone. *(v3: built so; the cheap path's check is the record's commit alone, B22, and a relaunch's before-start took 0.02 s, as-built §5.4.)* | C3 §4.2: both phases run on every launch, and the command must be fast and offline-safe when nothing changed. Checking the installed thing (not only a record) repairs a deleted runtime or a removed managed Python. | A "first launch done" flag (misses a deleted install). |
| F | **Setup owns four fields of the `deep_reasoner` agent profile** (`agent_kind`, `acp_server`, `acp_command`, `acp_subagents`) **and the `--home` pair in its arguments; it activates the profile once, when it first creates it.** Everything else in the profile, the spend cap included, is the user's after creation. *(v3: built so; the id comes from the profile's own GET, B25. Canvas `dr-3`'s onboarding keeps the active profile (#29), so a first launch does not undo the activation, and E12 pins that.)* | The profile's command path is stable (`runtime/current`), so a launch rewrites nothing. A user who switches the default agent, or raises the cap in Canvas's profile editor, is not overruled on the next launch. | Rewriting the whole profile every launch. Making it the default every launch. |
| G | **The Library App is staged on the user's machine** (*v2:* skeleton, no longer final): three of D3's built files from the runtime (`canvas-extension.json`, `dist/index.js`, `panel.svg`; not `ui/`, which `dr-library serve` serves itself), plus a backend artifact D5 generates, a `.tar.gz` holding one `/bin/sh` launcher that `exec`s `runtime/current/bin/dr-library`. Setup installs it from that local path, enables it once, and approves (`prepare`) and starts its backend on every launch. A failure here warns and does not stop the launch. | The agent-server requires the backend's executable inside the unpacked artifact and gives it six environment variables (`manifest.py:217–255`, `backend.py:38–40, 395–412`); `dr-library` imports deep_reasoner, which nothing we publish may contain, so the artifact can only be built where deep_reasoner is installed. The launcher script is the same bytes on every launch and both architectures, so its checksum and the approval survive upgrades. Stock Canvas has no control that starts an App backend, and backends do not survive an agent-server restart, so setup starts it. Conversations work without the panel, so the panel's failure must not block them. *(v2: D3 accepted this, D3 §8.4; staging only the App's own files keeps a UI-only change from changing the digest, which would force a reinstall.)* | Shipping a frozen `dr-library` binary (it would contain deep_reasoner). Installing from a git URL (the backend artifact must be built per machine). Leaving the start to D3's panel (a backend is not ready until its first open, and every first open would wait on deep_reasoner's imports; *v2:* the panel, as built, restarts one that died by starting its prepared revision, never by approving one, D3 decision F). |
| H | **The key proxy runs in `dr-acp`'s front, on its own thread, as a Starlette app under uvicorn on 127.0.0.1.** Per run it mints one 256-bit token per provider key it holds, one route per configured upstream, and gives the worker the token under the key's own variable name; it scrubs the worker's environment of the key by name and by value, and of the agent-server's secrets. | The spec places it there (decision 7). Its own thread keeps a slow upstream from delaying ACP traffic, and uvicorn installs no signal handlers off the main thread (`uvicorn/server.py`, `capture_signals`), so D1's SIGTERM shutdown is untouched. Starlette and uvicorn are already dependencies (D2). Reusing the variable name means anything that reads the key, a user's own code in a cell included, gets a token that works only through the proxy. | LiteLLM (heavy for one user, spec §2). A hand-written HTTP/1.1 server on `asyncio` (chunked transfer and keep-alive by hand). |
| I | **The cap is enforced, not estimated afterwards:** the proxy forwards only metered model endpoints; it reserves an estimate of each call's cost before forwarding and settles the real one after; it refuses a model whose price is unknown unless the upstream is on loopback. The ledger is per conversation (root ACP session) and persisted. *(v3: Michael's ruling, B4: a provider's refusal that reports no usage costs nothing. A body that is not a JSON object of at most 32 MiB is refused, B5.)* | A cap that a cell can step around through an unmetered endpoint (fine-tuning, batch, files), an unpriced model or twenty concurrent calls does not bound anything. A restarted `dr-acp` (the bridge restarts it after a slow Stop) must not reset the count. | Counting after the fact only (a `run_all` of 20 overshoots by 20 calls). Pricing unknown models at a fallback rate (a dearer model escapes the cap). |
| J | **The proxy is on by default in `dr-acp`** (`--no-key-proxy` turns it off); a client whose key `dr-acp` does not hold is left as configured. | Decision 7 says keys reach the worker only through the proxy. Keyless clients (a local vLLM, every one of D1's scripted tests) have nothing to protect, so D1's suite is unaffected. | Opt-in (a terminal `dr-acp` would leak by default). |
| K | **Telemetry is off in our builds**: the frontend is built with `VITE_DO_NOT_TRACK=1` and `telemetry.posthogApiKey` is emptied in the built `defaults.json`. *(v3: and with Canvas `dr-3`'s #28, a build that cannot report asks no consent and offers no analytics switch, B7.)* | Canvas sends an install event to OpenHands' PostHog without consent (`src/services/telemetry.ts:7–12`, unchanged since v1's pin), and the agent-server and automation backends default to the same key (`scripts/dev-safe.mjs:752–790`, `buildAgentServerTelemetryEnv`; `dev-with-automation.mjs:1070–1084`, `buildAutomationTelemetryEnv`). A packaged app is started without our build's environment, so only build-time values reach it: the bundle's `VITE_DO_NOT_TRACK` and `defaults.json`'s empty key, which the launcher reads as its default. Our users did not agree to report to a third party. | Shipping upstream's default. |
| L | **Product identity comes from a wrapper electron-builder config in this repo** (`desktop/electron-builder.dr.mjs`) that imports the fork's and overrides the app id, product name, `extraMetadata` and artifact names. *(v3: and one more key, `mac.minimumSystemVersion` `"14.0"`, B19.)* | No fork commit (the brief's rule); Electron's `userData` (the frontend's local storage) follows `extraMetadata.productName`, so it is separate from stock Agent Canvas (C3 §4.3). | A fork commit for our name. `-c.key=value` overrides on the command line (ambiguous beside `--config`). |
| M | **CI lives in this repo, and D5's workflows reach `main` with D5's PR stack, as D1's to D3's code did.** Until then `main` carries only what GitHub needs to start them: a copy of each on-demand workflow (`cross-repo.yml`, `desktop-release.yml`; `fork-live.yml` is there already, `633a00d`) and `nightly.yml`, a scheduled trigger that dispatches `cross-repo.yml` on `v1-desktop`, and on `main` once D5 has merged. *(v3: B26 and B11. `cross-repo.yml` now runs nightly on its own schedule, which takes effect once it is on `main`, and has no `has-d5`; #42 deletes `nightly.yml` from `main`. Until the stack merges, `main`'s copies (#34, #35), older than this branch's, run nothing, since `main` has no `desktop/pins.toml`.)* | GitHub requires an on-demand workflow's file on the default branch and runs a scheduled workflow only from it. A dispatched run uses the file at the ref it is dispatched on. A run started by the workflow token through `workflow_dispatch` is allowed to start another workflow. *(v2: v1 sent the nightly run to `self-hosted-v1`, the spec's integration branch (§5); D1 to D3 merged into `main` (#1–#26), so `main` is where merged work and its workflows live.)* | The nightly job's full definition on `main` before D5 merges (it would drift from the branch it tests). |
| N | **The App-backend ingress is `http://127.0.0.1:<agent-server port>`, which C3's launcher sets as a generic default** (*v2:* built, C3 #5, B2, `scripts/dev-safe.mjs:883–884`; approved by Michael as a scope addition to C3 on 2026-10-03). D5 sets nothing; v1's fallback in setup is gone. *(v3: E12 proves it in Electron's Chromium: D3's frame works through the bridge, its cookie partitioned under `http://localhost`, as-built §5.2.)* | The bridge answers 503 until an ingress origin is configured, and requires it to be a different origin from Canvas's (`canvas_extensions/bridge.py:231–244, 304–314`). The window loads Canvas from `http://localhost:8000` (`electron/main.mjs:399`), and the launcher binds the agent-server to 127.0.0.1 (`dev-with-automation.mjs:1126–1132`), so the agent-server's own address is reachable, keeps its `Host`, and is another origin and another site: Canvas's own cookies never reach an App backend. What stays D5's: showing in Electron's own Chromium that the frame keeps the bridge's cookie (E12 step 5). | `http://localhost:18000` (another origin but the same site, so Canvas's `localhost` cookies would travel with every App request; and `localhost` may resolve to `::1` where the agent-server listens only on IPv4). A second ingress process (one more port and service for what the agent-server already serves). |
| O | *(v2)* **`dr_app.texts` follows D1's and D2's rule: a constant is a sentence without fields, a function returns a sentence with its fields** (`texts.safety(cap)`, §6). D3's equality test changes one line with it: `texts.safety("7")` for `texts.SAFETY.format(cap=7)`. | The Code Guide forbids `.format()`; `deep_reasoning.acp.texts` and `deep_reasoning.library.texts` already work this way; D3 said its test follows whatever D5 writes (D3 B19, §8.4 item 7). The test stops skipping as soon as `dr_app` is a dev dependency, so the line changes in the same commit. | A `str.format` template, which D3's test assumed. |
| P | *(v2)* **`dr-app` leaves nothing running and holds nothing open.** It starts no process in a session or group of its own, and no background process; it runs each subprocess (`uv`, `git`, the runtime's Python) with its output on a pipe of `dr-app`'s own, copies the lines into the startup log, and goes on at the subprocess's exit, not at the pipe's end. The Library backend is started by the agent-server (its child, its own log), never by `dr-app`. *(v3: built so; the fetch of the commit's tree runs through `run_logged` too, B22.)* | C3 v3 §4.2: a phase ends only when the command's stdout and stderr close, so anything that keeps them (a credential helper that daemonizes, a stray grandchild) holds the phase, up to its 15 minutes, and then fails the launch. A quit signals the command's process group, so whatever `dr-app` started is stopped with it, unless it left the group. Every step is restartable (§4.4.3), so a quit or a timeout mid-install leaves nothing the next launch cannot repair. | Letting subprocesses inherit the launcher's output (any grandchild that keeps it holds the phase). `start_new_session` for the install (a quit could not stop it). |

### 1.2 The skeleton now, the final part after the rest

*(v2: rewritten.)* The task row says "skeleton first, final after the rest". Most of the rest has merged since v1, so
the skeleton is now everything that needs only merged code and the redone wiring, and the final part is only what
C1, C2 and D4 bring.

*(v3: both parts are built and run; read this section as v2's plan. Steps 1 to 5 went in this order, test-first. By
the time step 7's pins existed, C1, C2 and D4 had merged, so the final part was built in the same pass: E10 with D4's
server (`d2f42d4`), `canvas-replay` (`fe6a135`), D4's forwarding test (`e943977`) and E12's final steps (`518fb91`).
The Canvas pin went `dr-1` → `dr-2` → `dr-3` and the first release tag is still to come (B1). Step 6's files on `main`
are #34 and #35 (B11).)*

| Part | Skeleton (build now) | Final (waits on) |
|---|---|---|
| The build (§4.2) | all of it: pins and their checks, `build.py`, the wrapper config, the bootstrap, Linux and macOS packages | — |
| `dr-app setup`, before-start (§4.4) | all of it: the data home, the checks, the runtime install, the `bin/` links | — |
| `dr-app setup`, after-ready (§4.5) | the `deep_reasoner` profile with `acp_subagents: true` (S1, merged); the model-key hint; the Library App (§4.6; v1's final part: D3's package and S2's panels and macOS backends are merged) | — |
| The App-backend ingress (§4.9) | nothing to build (C3 B2); E12 shows the bridge's cookie in Electron's own Chromium with D3's frame (§7.5 step 5) | the panel in Canvas's header (**C2**) |
| The key proxy and spend cap (§4.7), E10's two tests (§7.1) | all of it, with the tool-client half of D1's seam (§8.1) | E10 again with **D4**'s `echo_server.py` bound in the worker (§8.7) |
| Export, `dr-app home` (§4.8) | all of it | — |
| The safety notice (§2.3) | the startup-log line at first install; the README; D3's frame shows it (merged), and E12 reads it in the real app | **D4**'s own sentence under it in the Tools tab |
| `fork-live.yml` (§7.4) | built and on `main`; dispatched again on `v1-desktop` once the proxy is in, with `sdk_ref` `dr-2` | — |
| `cross-repo.yml` (§7.5) | `pins`; `desktop-e2e`, E12's skeleton flow; `bridge-replay`, E5's second half (S1 merged) | `canvas-replay`, E6 (**C1**); E12's final steps: the nested tree and a Stop (**C1**); the namespace picker, the slash menu, Show decompositions, Create decomposition and the next conversation (**C2**); an MCP server (**D4**) |
| `desktop-release.yml` (§7.6) | the per-OS builds on demand, and the macOS launch smoke that waits for the Library backend (D3 and S2 merged) | the first release tag, once C1, C2 and D4 are in the pins |

**The skeleton's build order.** Steps 1 to 6 need only `main` at `1f9fe52` and the SDK fork at `34c540c`, so they
start now, in this order, each with its tests first. Step 7 is the first that waits, and only on what it must.

1. **D1's seam, its tool-client half** (§8.1), in D1's files: `RunSource.tool_clients`,
   `RouteGrant.tool_client_overrides`, `ModelRoute.grant(…, tool_upstreams=…)`, `Start.tool_client_overrides` and
   the worker's merge. The proxy's grant is written against it.
2. **The key proxy and spend cap** (§4.7, §5.7), `dr-acp`'s two options and `httpx` as a direct dependency, with
   `test_key_proxy.py` and E10's two tests (§7.1). Pure deep-reasoning.
3. **The `deep-reasoning-app` package** (§4.3 to §4.8, §5.1 to §5.6, §6): the workspace member and
   `runtime.lock.txt`, then layout and home, runtime, the agent-server client, the profile, the Library App, the CLI
   and texts, with §7.2's tests (stub `uv`, `uvx` and `git`; an in-test HTTP server answering like the
   agent-server). D3's one test line (decision O) changes in the commit that makes `dr_app` a dev dependency.
4. **`desktop/`** (§4.2, §5.8): `build.py` with every check behind injected readers, the bootstrap, the wrapper
   config, and `pins.toml` with `[sdk_fork]` filled (`34c540c`, tag `dr-2`) and `[canvas_fork]` a placeholder;
   §7.3's tests.
5. **Against the SDK fork's commit alone**, which needs no wiring (each test checks out `34c540c` and starts its
   agent-server directly): `test_canvas_app.py`'s `crossrepo` test (the staged artifact passes `prepare`, the
   backend answers `/health`) and E5's `bridge-replay` (§7.5), as `cross-repo.yml`'s first jobs.
6. **The files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`
   dispatching on `v1-desktop`; placed with Michael's yes, as `fork-live.yml` was.
7. **Waits on `dr-2`, the redone wiring (§8.6) and the Canvas fork's first tag**: fill `[canvas_fork]`;
   `build.py check` green (the `pins` job); the Linux packages; E12's skeleton flow (`desktop-e2e`);
   `desktop-release.yml` with its macOS smoke; `fork-live.yml` dispatched on `v1-desktop` with `sdk_ref` `dr-2`.

**The final part, in the order its pieces can land.** Each is a pin bump with the steps it enables, green in
`cross-repo.yml` before the pin moves (spec §2):
- **C1** merges into the Canvas fork's `deep-reasoning`, after merging the redone wiring, and the fork is tagged
  again: `canvas-replay` (E6) and E12's nested-tree step (§7.5, §8.4).
- **C2** likewise: E12's picker, slash-menu, header-panel and Create-decomposition steps (§7.5, §8.4).
- **D4** merges into `main`, and `v1-desktop` merges `main`: E10 with an MCP server bound, §2.1's exception, E12's
  MCP step and D4's forwarding test (§8.7).
- Then the first release tag (§7.6).

**What the skeleton needs from others** (v1's list, now settled): C3 merged with the ingress default (done,
`7c12afb`); D1, D2 and D3 merged (done, `1f9fe52`); S1 with the profile's opt-in (done, SDK #13); the SDK fork's
release step (done, #18). Still needed: `dr-2` pushed, so that its release carries the tarball; the redone wiring
merged into the Canvas fork's `deep-reasoning`; a Canvas tag at it. No pin runs a pre-S1 agent-server any more,
so v1's flat fallback is gone (§4.5.1).

### 1.3 What D5 owns, and its seams

- **Owns:** `desktop/` (pins, build, wrapper config, bootstrap); the `deep-reasoning-app` package and the `dr-app`
  command; `src/deep_reasoning/acp/proxy.py` and the two `dr-acp` options that use it; the workflows `fork-live.yml`
  (built), `cross-repo.yml`, `desktop-release.yml` and `nightly.yml`; E10, E12, and the cross-repo halves of E5 and
  E6; the README's install section. *(v3: `nightly.yml` is gone from D5's files, B26; the README is the whole root
  `README.md`, B18; and D5 owns the macOS launch smoke, `tests/desktop/test_launch_smoke.py`.)*
- **Seam to C3** (C3 v3 §4): D5 writes `paths.stateDir` and `setup` into a build checkout's `defaults.json` and relies
  on §4 as v3 states it, the ingress default (B2) and the end of a phase (decision P) included. *(v2: v1's ask
  for the ingress default is built, §8.5.)*
- **Seam to D1** (§4.7, §8.1): `ProxyRoute` implements `ModelRoute`; D5 extends it additively so tool clients are
  routed too. *(v2: the name v1 asked for is already in `ALWAYS_REMOVED`.)*
- **Seam to D2**: `dr-library serve --port P --home DIR` (the backend's argv), `dr-library export DIR --home DIR`,
  `/health`, and D2's set of refused filesystems (mirrored, pinned by a test). No change to D2.
- **Seam to S1** (§8.2): the profile's `acp_subagents`; the scripted agent's `--transcript` mode for E5. Both merged.
- **Seam to D3** (§8.3): the three files D5 stages and the `backend` block it adds; `texts.safety`, which D3's
  test compares; the backend's start, which D3's page repeats for a backend that died.
- **Seam to C1, C2** (§8.4): C1's replay hook for E6; their stable test ids for E12. Adopted, not merged. *(v3:
  merged, Canvas #13–#26, and E12 drives them, B1.)*
- **Seam to D4** (§8.7): E10 with an MCP server bound; the profile's `mcp_server_refs: null`. *(v3: built, B9.)*
- **Seam to the SDK fork's release** (§8.6): a `dr-N` tag on `deep-reasoning` and the tarball its release carries.

---

## 2 · Safety: what the app protects, and what it does not

The agent runs model-written Python as the user, with the whole disk and network reachable, as `dr` does today
(spec §2, decision 7). The key proxy runs as the same user. So the app has two kinds of protection: against
**accidents and opportunistic injected code** (a key that ends up in a log, a transcript, a cell's printout, an
`env` dump a model was talked into making; a loop that spends without end), which it holds; and against **a
cell that sets out to defeat it**, which it does not. This section says which is which, and the app says the
same to the user (§2.3).

### 2.1 What it protects

| Property | How | Proven by |
|---|---|---|
| A provider key `dr-acp` holds is not in the worker's environment, a cell's `os.environ` or `/proc/self/environ`, any process the worker starts, the transcript, or the run log. *(v2, from D4 §5 and §11.4, final part: one exception, by the user's configuration: a stdio MCP server whose Canvas settings name the key in its `env` gets it.)* | The worker gets a token under the key's name; every variable whose value contains a held key is removed (§4.7.2); upstream error bodies are redacted before they reach the worker; the proxy never logs headers | E10 #1 (§7.1), and again in the real app (E12); with an MCP server bound once D4 merges (§8.7) |
| The agent-server's own secrets (`OH_SECRET_KEY`, `OH_SESSION_API_KEYS_*`, `SESSION_API_KEY`, and `OPENHANDS_AUTOMATION_API_KEY`, which the launcher sets to the session key, `dev-with-automation.mjs:1066`) are not in the worker's environment | Removed by name (D1's `ALWAYS_REMOVED`, merged with all four, D1 B2) and, by D5, by value | E10 #1; D1's `test_route.py::test_the_agent_servers_secrets_never_reach_the_worker` |
| Spending through the proxy stops at the conversation's cap | Endpoint allow-list; unpriced models refused; reservations before forwarding; a persisted ledger per conversation (§4.7.3) | E10 #2 |
| A token is worth nothing outside its run | Tokens are 256-bit, bound to one run's routes, dropped when the run ends; a route forwards only to the upstream the config named, so a cell cannot send the key to a host of its choosing | §7.1 units |
| Other OS users on a shared machine cannot spend through the proxy | It listens on 127.0.0.1 and needs a token | §7.1 units |
| Canvas's own cookies and scripts do not reach an App's frame, nor the frame Canvas's | The App-backend ingress, C3's default, is another origin and another site than Canvas's (§4.9); the bridge admits a frame's request only with that App's five-minute HttpOnly session cookie (`bridge.py:33, 448–472`) | E12 step 5 (§7.5), with D3's frame |
| Nothing of deep_reasoner is in anything we build or publish, and no read token ships | deep_reasoner is installed on the user's machine with the user's credentials (§4.4); CI's token lives in Actions secrets | the build's artifact check (§4.2) |
| No usage reports go to a third party | Telemetry off at build time (decision K) | §7.3 |

*(v3: every row holds as built. The tests that prove each are named in "Which tests carry which property", Part 1,
and E12 repeats rows 1, 2 and 6 in the installed app. Row 7 is also Michael's ruling, B16: the GitHub sign-in stays in
every build and release, so deep_reasoner is installed on the user's machine with the user's git credentials and
never ships inside the app. Row 7's check runs in every build; no unit test pins its refusal.)*

### 2.2 What it does not protect

A cell runs as the user. Everything below is reachable by a cell that tries, and the cap and the token do not
change that.

- **Every Canvas secret, provider keys included.** `~/.deep-reasoning/canvas/secrets.json` is encrypted with
  `…/agent-canvas/secret-key.txt`, which the user (so the cell) can read.
- **The agent-server itself.** `…/agent-canvas/api-key.txt` is the session key. With it, any client may read
  every secret in plaintext (`X-Expose-Secrets: plaintext`, `settings_router.py:120–140`; `GET
  /api/settings/secrets/{name}`, `:492`), install and approve Apps, and change agent profiles, the spend cap
  included. The frontend's local storage holds the same key.
- **Other processes' environments.** On Linux `/proc/<pid>/environ` of `dr-acp` and of the agent-server is
  readable by the same user; both start with the keys in their environment (the bridge passes the conversation's
  secrets to `dr-acp`, `acp_agent.py:3306–3331`).
- **The cap, by a cell that attacks it:** it can edit `spend/<session>.json` and kill `dr-acp` (the bridge
  restarts it, and the ledger is read again), raise `--spend-cap-usd` in the profile for later conversations, or
  read a key and call the provider directly. The cap bounds what is spent through the proxy, by code that does
  not set out to defeat it.
- **The user's files.** The conversation's folder is only the worker's working directory, not a boundary: a cell
  can read and change any file the user can (SSH keys, cloud and `gh` credentials, `.env` files, other projects).
- **The network.** A cell can reach anything the user's machine can.
- **The user's other secrets reach the worker on purpose.** A Canvas secret that is not a provider key the proxy
  holds (a `DAYTONA_API_KEY` for a remote REPL, a `GITHUB_TOKEN` for a tool) stays in the worker's environment,
  because tools need them. The `deep_reasoner` profile's `secret_refs` is `null` (all of the user's secrets reach
  `dr-acp`); a user who wants fewer edits it.
- **A key a cell prints after reading it from disk** lands in our run log. (The agent-server's transcript masks
  the values of Canvas secrets in ACP output, `acp_agent.py:3299`; our run log does not; §11 item 9.)
- **Tools and MCP servers** (D4) are programs that run as the user (spec D4); D4 §5 says plainly what each can
  reach, and a stdio MCP server gets whatever its Canvas settings give it, a provider key included.
- *(v2)* **A Claude Code backbone on the machine's own login.** deep_reasoner starts `claude` with its own
  environment minus every `CLAUDE_CODE*` variable (`v2/claude_code.py:285–307`; D1's EXP-27), and the bridge removes
  `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from `dr-acp`'s environment whenever `CLAUDE_CODE_OAUTH_TOKEN` is a
  secret (`acp_agent.py:3035–3058`, `settings/acp_providers.py:537–542`: a `custom` server gets every provider's
  rule). Such a `claude` then calls Anthropic on the login stored in its own configuration, which neither the key
  proxy nor the cap sees (§11 item 3).
- **The Library's backend on macOS** is unauthenticated loopback HTTP that any local user could reach (D2
  decision K and its §9 item 1; on Linux D2 refuses other users' connections; on both, its `Host` check, D2
  as-built §2 #1, stops a rebinding web page, not a local process).
- **The download.** The app is unsigned; on macOS the user clears the quarantine flag by hand (§4.2.6), so they
  trust whatever they downloaded. Releases are assets of a private GitHub repository. *(v3: deep-reasoning is public,
  and so are its release downloads, Michael's ruling, B15; deep_reasoner_beta stays private, B16.)*

### 2.3 Where the user is told

- **The startup log, at the first install** (the splash shows it): §6's `safety(cap)`, with the cap in force.
- **The decompositions panel, the first time it opens, and its Tools tab** (spec D5): the same sentence, with an
  "I understand" button. *(v2: built by D3, merged: the cap read from the profile's `--spend-cap-usd`, 5 when
  absent, and `SAFETY_NO_CAP` when the profile has `--no-key-proxy`; D4 adds its `TOOLS_RISK` under it in the Tools
  tab, final part.)*
- **The README's install section**: §2.2 in short, with how to uninstall (§4.8.3).

*(v3: all three are built: the startup log's `safety` line at a first install, D3's notice in the panel and the Tools
tab with D4's risk line under it (E12 reads both in the real app), and the README's "What the app protects, and what
it does not". Michael has asked to revisit these warnings in a later UX round, TASK-42, done with his other UI
requests; that is not D5's, and D5 ships them as this section says, B17.)*

---

## 3 · Where this design departs from, or adds to, the approved spec

Each is a refinement inside D5's scope unless it says otherwise. If the Conductor reads any as a change of what
was approved, it goes back to Michael.

1. **The setup command is an `sh` bootstrap around a separate small package** (decision B), not `dr-app` from
   the main package; the spec's three first-launch failure messages are kept, and the one for deep-reasoning
   itself is new (deep-reasoning is private too, spec D5's evidence). *(v3: deep-reasoning is public, so that line
   now asks only that the computer be online, B15.)*
2. **Who can install v1:** people with read access to **both** deep_reasoner_beta and deep-reasoning (the
   release assets and the setup's fetch), until Michael makes deep-reasoning public. The spec names only
   deep_reasoner_beta. *(v3: deep-reasoning and its release downloads are public, B15, so it is now as the spec
   says: read access to deep_reasoner_beta, with the user's own git sign-in, which stays in every build and release,
   B16.)*
3. **The state directory is `~/.deep-reasoning/canvas/agent-canvas`,** not the mock-up's
   `~/.openhands/deep-reasoning` (C3 §2.4 and §4.3).
4. **The runtime is installed from a committed export of `uv.lock`** (decision C). The spec says "installs
   deep-reasoning at its pinned commit with uv"; this fixes every transitive version too. *(v3: superseded by B22:
   `uv sync` of the commit's own tree, which fixes every version through the commit's `uv.lock`, with no export.)*
5. **The data home moves to `/var/tmp/deep-reasoning-<uid>` on a network home directory,** with `dr-app home` to
   choose another (D2's ruling made concrete; §4.4.1).
6. **Telemetry is off** in our builds (decision K). The spec does not mention it.
7. **Setup builds the App's backend artifact on the user's machine and starts the backend on every launch**
   (decision G). The spec says setup "installs and enables the Library App"; approval and start were implied by
   its evidence ("starts its backend only once its revision is approved").
8. **The key proxy fails closed on an unpriced model, forwards only model endpoints, reserves before
   forwarding, and routes tool clients and the Claude CLI too** (decisions H and I). The spec gives the proxy
   ≈150 lines and leaves its Anthropic passthrough and cap to the System Designer.
9. **A refused call is HTTP 402,** which neither the OpenAI client nor the Claude CLI retries, so the agent fails
   at once with the proxy's sentence.
10. **`uv run desktop/build.py`**, not the mock-up's `make desktop` (no Makefile for one line).
11. **The build pins uv's version** (`UV_VERSION`), which upstream's download script otherwise takes as the latest
    release (C3 §4.4). *(v2: 0.12.23, the release C3's live test last proved the offline relaunch on, §4.2.1.)*
12. **`~/.deep-reasoning/bin` holds `dr-app` and `dr`;** setup does not edit the user's `PATH` or shell files, so
    the mock-up's `dr-app export …` is `~/.deep-reasoning/bin/dr-app export …` until the user adds that
    directory to their `PATH` (the README says how).
13. **E12 gains four checks** the spec does not list: E10's properties inside the real app, a relaunch of setup
    with the network cut, the App-backend bridge's cookie in Electron's Chromium (*v2:* with D3's own frame, which
    replaces v1's probe App), and *(v2)* a quit that leaves nothing of the setup command running. *(v3: built, among
   E12's seventeen tests, with three more on onboarding and consent, B7.)*
14. **The CI is split across three workflows plus trigger files on `main`** (decision M), and owns the shared
    live workflow S1 and S2 asked for (S1 §7.4, S2 §9). *(v2: that workflow, `fork-live.yml`, is built, on `main`,
    and carried S1's and S2's live tiers, §7.4. D5's other workflows reach `main` with its PR stack; v1 said
    `self-hosted-v1`, the spec's §5 branch, which the merged work did not use.)* *(v3: two workflows, `cross-repo.yml`
    with its own schedule and `desktop-release.yml`, and no trigger file once the stack merges, B26, B11.)*
15. **Size:** ≈2.7k lines with tests and about 8–9 h at Gate C, against the spec's ≈1.2k and ≈4 h (§10). *(v2:
    ≈2.6k, about 8.5 h; §10.)* *(v3: built at 6,512 reviewable lines, 2,589 of code and 3,923 of tests, and the
    README's 161: about 22 h at Gate C at ≈300 lines an hour. §3.1, "Size".)*
16. ~~**The App-backend ingress is configured** for the desktop app by a generic launcher default in the Canvas
    fork, beyond C3's approved scope.~~ *(v2: no longer a departure of D5's. Michael approved the default as a
    scope addition to C3 on 2026-10-03 (spec, "Scope additions approved" (2)), and C3 built it (#5, B2).)*

### 3.1 Changed by the build, and Michael's rulings since v2

*(v3; new.)* Every departure the as-built r3 records (its §1.1 #1–#25, §1.2's stale lines, §1.3, §6 and §8) and every
ruling Michael made since v2, each with its commit, its reason and the test that pins it. Where a later change
superseded an earlier one, both are here and the later says so. The sections each names carry a v3 note in place.
B-numbers are this design's; each item names the as-built's numbers it answers.

**(a) The build, to Gate B** (`f106a0c` … `3c923aa`, 2026-10-04)

B1. **Both parts in one pass, and the pins that came of it** (as-built §1.2). C1, C2 and D4 merged while the skeleton
was being built, so the final part was built with it: E10 with D4's server (`d2f42d4`), `canvas-replay` (`fe6a135`),
D4's forwarding test (`e943977`) and E12's final steps (`518fb91`). The Canvas pin followed the fork's tags: `dr-1`,
`fc87687`, the redone wiring (`2f55b18`); `dr-2`, `9d050ab`, with C1, C2 and a toast fix, #27 (`5fc05eb`); `dr-3`,
`4355a36`, with #28 and #29 (`f32e152`). The SDK pin stayed `34c540c`, `dr-2`. The `.deb`'s maintainer is Michael's
git identity on this repository (his ruling, `2f55b18`). No release tag exists yet. Sections: §1.2, §4.2.1, §8.4,
§8.6, §9 (W1, C1, C2, D4), §11 items 1, 2, 13, 17. Tests: `build.py check` in the `pins` job; and B12's two.

B2. **The runtime venv is relocatable** (#3; `622976b`). `uv venv --relocatable --managed-python`: without it uv
writes each entry point with an absolute shebang to `runtime/<commit>.tmp-<pid>`, and after the rename every runtime
command was dead (`dr-library` exited 127 as the App's backend at E12's first launch). §4.4.3. Test:
`test_runtime.py::test_the_runtimes_commands_run_from_where_the_install_leaves_them`.

B3. **A fourth rule for the data home: room for a Claude run's socket** (#4; `b1e3df2`). deep_reasoner's Claude
backbone serves `<run dir>/repl.sock`, and each Claude sub-agent one level below it; a Unix socket's path holds at
most 107 bytes on Linux and 103 on macOS. `choose_home` and `dr-app home DIR` refuse, exit 13 with `home_too_long`,
a home whose deepest such socket (`runs/<run id>/children/<n>/repl.sock`, the home plus 52 bytes) would pass the
limit. The default homes fit (on macOS, user names up to 28 characters); a HOME under macOS's `$TMPDIR` does not.
Upstream it is DR5 (TASK-47, deep_reasoner_beta#113). §4.4.1, §4.8.2, §5.1, §6. Tests:
`test_layout.py::test_a_home_too_long_for_a_claude_runs_socket_is_refused`,
`::test_setup_refuses_a_default_home_too_long_for_a_claude_runs_socket`,
`::test_linuxs_limit_is_where_a_socket_stops_binding`;
`test_cli.py::test_home_refuses_a_folder_too_long_for_a_claude_runs_socket`.

B4. **Michael's ruling: a provider's error that reports no usage costs nothing** (#5; `f385025`, 2026-10-04). Usage
reported, at any status, is charged; no usage on a 2xx keeps the reservation as the cost; no usage on a non-2xx is 0,
the reservation released; an unreachable upstream is 0, as v2 had it. Before, the OpenAI client's four retries of a
500 left five reservations standing as spend, and under a cap of five calls the next good call was refused 402.
Decision I, §4.7.3. Tests: `test_key_proxy.py::test_provider_errors_release_their_reservations`,
`::test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused`.

B5. **The proxy refuses a body it cannot read, and passes bodies uncompressed** (#6; `f198777`). A body that is not a
JSON object, or is over 32 MiB, is refused 400 `bad_body` (`texts.bad_body(rest, mib)`); v2 named neither the refusal
nor its sentence. `Accept-Encoding` is not forwarded and `Content-Encoding` not returned, so every response passes
plain; the client's own `Authorization` and `x-api-key`, which carry the token, are not forwarded either. The build
recorded no reason; this design's reading is that the proxy meters from the response's body, which compression would
hide. An Anthropic route sends the key as `x-api-key`. §4.7.3, §6. Test:
`test_key_proxy.py::test_an_anthropic_route_swaps_the_x_api_key`. No test pins `bad_body` or the uncompressed path.

B6. **Sentences §6 lacked** (as-built #15, #19, #20; `5425b62`, `b1e3df2`, `930a0cf`, `8125fa1`, `bd6e170`,
`e5c8be2`, `f198777`). `dr_app.texts` gains `NO_AGENT_SERVER` (after-ready without the launcher's variables, exit 2),
`home_refused` (`dr-app home` given a relative path or a network filesystem), `home_too_long` (B3),
`state_from_a_newer_app` and `state_unusable` (B21); the proxy's texts gain `bad_body` (B5); the build's checks have a
sentence each, as §6 said, plus `wrong_machine` and `not_arm64` (B14) and `opens_too_early` (B19). §6 now lists every
one verbatim. Tests: each sentence's refusal test; `tests/app/test_texts.py` and `tests/acp/test_texts.py` compare
v2's sentences with fields, not these.

B7. **E12 is seventeen ordered tests on one launch** (#12; `b797abf`, `518fb91`, `1a90887`, `d39be70`, `c538fb3`,
`8ce99b2`). The module launches the installed app once with a fresh HOME, and its tests run in file order, each on
what the one before left. Where they differ from §7.5: the first conversation is onboarding's hello, since Canvas
`dr-3`'s #29 offers `deep_reasoner` first and chosen, not a dismissed onboarding; two tests the design did not list
pin that no consent dialog shows (a fixed 5 s wait) and that nothing records consent and Settings offers no analytics
switch (#28); the Library's config is written by the test (there is no `tests/desktop/e12/main.yaml`); Stop's plan
spawns the done sibling first and holds the grandchild's model call until `dr-acp` logs `stop.accepted` (whether
`run_all`'s children progress while one call waits is TASK-38, D1's); costs are compared with each sub-agent's cost
in the run log at its end; the next conversation asks a plain question once the slash menu offers the command; the
cookie is read with `Storage.getCookies`; the MCP server is added with `POST /api/settings/mcp/echo` and the Tools tab
reopened; the quit test asks that no process's command line names the fresh HOME. §7.5, §11 item 10. Tests: Part 5's
E12 row.

B8. **The macOS launch smoke is two tests, and the launch tests' fresh HOME stores no git credentials** (#13, §1.3 #5;
`9ca1f70`, `bd6e170`, `269c7af`, `ae363b4`). One launch: `app_ready(…, "installed")` in the log, the backend `ready`,
the app quits with 0; and the launched executable and its bundled uv are arm64 only (B14). The smoke's first runs
waited 15 minutes on a keychain dialog: the runner's system git config names `osxkeychain`, and under a HOME with no
keychain git's store asks where to keep the token. A user's HOME has a keychain, so the fix is the test's: an empty
credential helper ends the fresh HOME's git config. What it showed about the app, that the splash says nothing while
git waits, is TASK-39. A failed wait says why, with the log's last lines. §7.6, §11 item 14. Tests:
`test_launch_smoke.py`'s two;
`test_app.py::test_git_under_the_fresh_home_stores_no_credentials_whatever_the_systems_helper`,
`::test_a_failed_wait_says_why_with_the_logs_last_lines`.

B9. **E10 with D4's MCP server bound** (#16; `d2f42d4`). As §8.7 asked, with one difference: the server's environment
is its settings plus `mcp`'s six and `LC_CTYPE`, which D4's stdio guard, a Python, adds when it coerces a C locale
(PEP 538). It runs twice, with and without the model key named in the server's settings. §7.1, §8.7. Test:
`test_e10_keys.py::test_an_mcp_server_gets_a_provider_key_only_when_its_settings_name_it_and_the_worker_never_does[unnamed, named]`.

B10. **`cross-repo.yml` at Gate B: six jobs** (as-built #10, first half; `57c019d`, `bdfe042`): `has-d5`, so that
`main`'s copy (decision M) skips on a tree without `desktop/pins.toml`, and `library-app`, the Library App's
`crossrepo` test, besides §7.5's four. Superseded by B26.

B11. **`main`'s workflow copies are older than the branch's** (as-built #11, §6 #7 and #12; #34 `b2a74e0`, #35
`f1ca641`). `main` holds `cross-repo.yml` with `has-d5`, `library-app` and `bridge-replay` only; `desktop-release.yml`
building `mac-universal`, which `build.py` has refused since B14; and `nightly.yml`. None of them runs a job while
`main` has no `desktop/pins.toml`. The stack replaces them: #42 (`cross-repo.yml`, and `nightly.yml` deleted) and #43
(`desktop-release.yml`), with `desktop/pins.toml` first, in #40 (B26). Decision M, §7.5, §8.6, §11 item 8.

B12. **The default suite needs the network, and two tests restate the pins** (as-built §1.3 #2, #3; `2e883e7`,
`2a7b0ec`, `2f55b18`). `test_runtime.py::test_the_runtime_lock_installs_on_every_platform_the_app_ships_for`
dry-runs `uv.lock`'s registry packages, wheels only, for Linux x86-64 and macOS 14 arm64 against PyPI's metadata, with
no marker: the app must build nothing on a user's machine, which may have no compiler.
`test_build.py::test_the_committed_pins_load` and `::test_the_committed_sdk_pin_is_34c540c_tagged_dr_2` restate
`pins.toml`, so a pin bump edits them. §7.2, §7.3.

**(b) Gate B, and Michael's rulings** (2026-10-04 and 05; his words from the review ledger)

B13. **Gate B: approved.** Michael ran the `3c923aa` build in a macOS 26 VM: "It runs good btw generally." The
Conductor recorded it as approval, and he did not object when told so. No code.

B14. **Intel Macs dropped** (as-built #1; `bd6e170`, with `3500f87` undoing the Intel lock holds `2e883e7` and
`a4a9336`): "lets drop the intel macs no worries. we will go public with the deep reasoner code at some point no
worries for now." `build.py`'s targets are `linux` and `mac-arm64`, each only on its own machine (Linux x86-64, macOS
arm64), since the Canvas fork packages its uv and Node for the machine it builds on. `verify()` requires
`deep-reasoning-<version>-arm64.dmg` and `lipo -archs` = `arm64` for the `.app`'s Electron, uv and Node;
`desktop-release.yml` has no Intel job. §1 item 1, §4.2.4, §5.8, §7.6. Tests: Part 4's Mac row, and
`test_launch_smoke.py::test_the_mac_app_and_the_runtime_it_ran_are_arm64_only`.

B15. **deep-reasoning is public, and so are its release downloads** (as-built #7, #8; `3c923aa`, `bd6e170`): "public
downloads are fine", as the as-built records his words. Only deep_reasoner_beta needs read access. The bootstrap's
fetch-failure line no longer asks for access ("✗ Could not fetch github.com/michaeltheologitis/deep-reasoning: check
that this computer is online, then restart. Nothing was installed."); no workflow adds an `insteadOf` line for
deep-reasoning (DeanLight's stays); a tag's release is public. §2.2, §3 items 1 and 2, §4.3.1, §6, §7.5, §7.6. Tests:
`test_bootstrap.py::test_an_unreachable_deep_reasoning_says_so_and_keeps_uvx_status`,
`::test_dr_apps_own_failure_passes_through_without_the_fetch_line`.

B16. **The GitHub sign-in stays in every build and release**: "lets keep this login thing for when we are ready and we
will lift it when time comes", and "we keep github login for this NOT to happen" (deep_reasoner shipping inside the
app). It is the design as built (decision B, §2.1 row 7, §4.4.2): setup installs deep_reasoner on the user's machine
with the user's own git credentials, after checking that they can read deep_reasoner_beta, and nothing we build or
publish contains it. Lifting it is TASK-45, tied to no release, which starts only when Michael says Dean's code may go
public. No code.

B17. **His UI requests go to a later UX round, not into D5**: "Put them as tasks actually for when we make changes
again so we do them together." TASK-42 (the safety warnings, which would reverse §2.3), TASK-43 (the panel's button in
the dark theme), TASK-44 (the name "Deep Reasoning" wherever a user reads it), TASK-46 (the first message's auto-title
error, from the agent-server); TASK-50 (no agent choice anywhere), filed after Gate B, belongs to the same round. And
"dont start anything after we finish what we're doing now": nothing beyond D5 starts without his go. No code.

B18. **The four fixes as-built r1 proposed** ("yeah do the four u recommended!"). **The first: the README** (as-built
#9, #18; `c9bb7fe`, corrected by `3919e92`). A root `README.md`, also the package's long description, holds the
install section §1.3 and §2.3 ask for and what a user also needs: setup's own access check to run in a terminal;
where a credential helper must sit on a Mac; the `.AppImage`; a hand-run build's artifacts; onboarding (keep
`deep_reasoner`, press **Close** on **Say hello**, add `OPENAI_API_KEY`); how to change the cap; Electron's folders in
uninstall; and §2.2 in short. Where §2.2 is stale it follows the build (B15). `3919e92` corrected r2's findings: the
install's timing as the runs show it, no release before the first tag, the whole data table, `dr-app home`'s length
limit. §1.3, §2.3, §3 item 12, §4.2.6, §4.8.3. Tests: `test_readme.py`'s eight.

B19. **The second: macOS 14, enforced** (as-built #2, #19; `e5c8be2`). The runtime's locked packages install on Apple
silicon only from macOS 14 (onnxruntime 1.30.0, deep_reasoner's through chromadb, ships `macosx_14_0_arm64` wheels
and none older). The wrapper config's `mac` block declares `minimumSystemVersion: "14.0"`, and `verify()` refuses a
`.app` whose `Info.plist` declares any other `LSMinimumSystemVersion` (`opens_too_early`). That macOS 13 then refuses
to open the app is Apple's handling of the key, not run. §4.2.4, §5.8, §6. Test:
`test_build.py::test_a_mac_app_that_opens_before_macos_14_is_refused[12.0, 13.0, None]`.

B20. **The third: check 8 on a reused `--work`** (as-built #21, §1.3 #1; `24646d0`). A kept fork cache's refetch
moved only `FETCH_HEAD`, so a local check could refuse a pin merged after the first clone; the refetch was fixed.
Superseded by B24, which removed the cache, and this fix's test with it.

B21. **The fourth: a `setup.json` this app cannot use is explained, exit 14** (as-built #20, §1.3 #4; `930a0cf`, then
`8125fa1` for r2's §6 #9). An integer `v` above 1 gives `state_from_a_newer_app`; any other unusable file gives
`state_unusable` with one of six reasons (it cannot be read, it is not JSON, it is not a JSON object, its version is
…, it has no version, it holds a record this app does not write). Exit 14 is in the bootstrap's trusted 10–19 band, so
the bootstrap adds nothing. §4.3.2, §5.1, §6. Tests:
`test_layout.py::test_a_setup_state_this_app_could_not_have_written_says_why`,
`::test_a_setup_state_that_cannot_be_read_says_why`;
`test_cli.py::test_a_setup_state_it_cannot_use_is_explained_and_exits_14`.

**(c) The Scout's findings and the literate refactor** (after Behaviour Approved; `d9b35f4` … `3e9cee9`, 2026-10-05)

B22. **The runtime is `uv sync` of the commit's own tree** (as-built #22; `d9b35f4`, the Scout's finding 3).
`fetched_source` fetches deep-reasoning's tree at the commit into `runtime/<commit>.tmp-<pid>-source` (`git init`,
`git fetch --depth 1 <repo> <commit>`, `git checkout FETCH_HEAD`, each through `run_logged`); `deep_reasoner_pin`
reads deep_reasoner's URL and commit from that tree's `uv.lock`; `install_runtime` makes the relocatable venv (B2),
then runs `UV_PROJECT_ENVIRONMENT=<venv> uv sync --frozen --no-dev --no-editable --all-packages --project <tree>`, the
import check, the rename and the link; the tree is removed, success or not. `runtime_is_current` compares the commit
only, which fixes its `uv.lock`. `RuntimeRecord.lock_sha256` is still written and no check reads it, so a
`setup.json` from `3c923aa` or `c9bb7fe` still loads. Gone: `runtime.lock.txt` (176 generated lines), `RuntimeSpec`,
`LOCK_RESOURCE`, and check 7 with its machinery. The installed set is the same 173 packages at the same versions as
`3c923aa`'s exported lock gave (as-built §5.4). The reason: the lock CI tests is the one users install, with no second
copy to keep equal. Decision C, §3 item 4, §4.2.2 check 7, §4.4, §4.4.2, §4.4.3, §5.2. Tests: Part 2's install rows;
new, `test_runtime.py::test_deep_reasoners_pin_is_read_from_uv_lock_as_pyproject_names_it` and
`::test_the_runtimes_uv_sync_reads_no_project_setting_that_changes_its_set`; renamed,
`::test_a_first_launch_checks_then_installs_the_commits_own_lock` and `::test_a_new_commit_reinstalls`; gone with the
file, `test_the_runtime_lock_matches_uv_lock`.

B23. **The checks run in a new order, so two of setup's error paths changed** (as-built #23, §6 #11; `d9b35f4`).
**This moves behaviour Gate B approved, §4.4.2's order, through an adopted Scout finding.** The order is now git's
version, `uv` on `PATH`, the fetch of deep-reasoning's tree, then deep_reasoner's readability (its URL is in the
fetched `uv.lock`), then `checks_ok`, the safety line and `installing`. What a user sees, before (`3c923aa`) and now,
as the as-built ran each on both `dr-app`s (its §5.4):
- *Offline, when `uvx` already has this `dr-app` but the runtime is not current* (an interrupted first launch, a
  deleted runtime). Before: exit 10, `no_access_dr` ("✗ Could not read github.com/DeanLight/deep_reasoner_beta with
  your git credentials. It is private: ask Dean for read access, …"). Now: exit 11, git's own `fatal: unable to
  access 'https://github.com/michaeltheologitis/deep-reasoning/': …`, then `install_failed` naming `git fetch` ("…
  After an update this needs the network once: connect and restart."). A first launch offline with nothing cached is
  unchanged: `uvx` cannot fetch `dr-app`, and the bootstrap says to check the network.
- *deep-reasoning unreachable.* Before: exit 11 naming `uv pip sync`, after `checks_ok` and the safety line had
  printed. Now: exit 11 naming `git fetch`, before any check line.
- *deep_reasoner unreadable.* Exit 10, `no_access_dr`, before and now; now after a silent fetch of deep-reasoning's
  tree, which is removed. Nothing is installed.

For Gate C: in the first case the new sentence is the more accurate one (the machine is offline; nothing says the
user lacks access), so this design takes the new order as built. §4.4 steps 3–5, §4.4.2. Tests:
`test_runtime.py::test_a_failed_install_keeps_current_and_exits_11[git fetch, uv sync]`,
`::test_an_unreadable_deep_reasoner_installs_nothing` (now asserts `runtime/` empty rather than absent, since the
fetch makes it first), `::test_without_uv_nothing_is_installed`. A failing `git fetch` stands for the offline case in
the tests; the offline case itself is the as-built's probe.

B24. **Checks 4 and 8 read the forks through GitHub, and check 7 is gone** (as-built #14, #21, §1.3 #6; `f28730d`, the
Scout's finding 4; check 7 with B22). Check 4 reads the SDK fork's `uv.lock` at its commit from
`raw.githubusercontent.com`. Check 8 asks `repos/<fork>/compare/<commit>...deep-reasoning`: `ahead` or `identical`
passes, any other status or a 404 refuses, and `GITHUB_TOKEN`, when set, authenticates (the `pins` job and the
release jobs pass it). The blobless clones under `--work` are gone, with the class of bug B20 fixed; `--work` holds
only the Canvas checkout. Check 2 is two sentences (the repository, the commit), and check 5 asks only that
`paths.stateDir` and `setup.command` be null, since the fork sets `setup.phases`. The gap: the two readers have no
unit test, and an HTTP error other than check 8's 404 (GitHub allows 60 unauthenticated requests an hour) ends
`build.py` in a traceback (§11 item 19). §4.2.2, §5.8. Tests: Part 4's pins row, the readers injected; `build.py
check` against the real forks in the `pins` job.

B25. **The profile's id comes from its own GET** (as-built #24; `9002014`, the Scout's finding 5). `GET
/api/agent-profiles/deep_reasoner` returns the profile with its id; setup reads it there, and again after a write
for the id the server kept or minted, and no longer lists the profiles. v2's reason for listing, that upstream seeds a
default profile into an empty store and ours should be activated after it, never applied: setup has written
`deep_reasoner` before any listing, and the seeding needs an empty store. A relaunch makes one request where it made
two. §4.5.1 steps 3–4, §5.4. Tests: `test_profile.py::test_a_relaunch_writes_nothing`; E12's first test checks the
active pointer.

B26. **`cross-repo.yml` is D5's own: §7.5's four jobs, and its own schedule** (as-built #10; `146bbbf`, the Scout's
findings 1 and 2). `has-d5` and its `needs`/`if` lines existed only so that `main`'s older copies would skip on a tree
without `desktop/pins.toml`; they are gone from both workflows. `library-app`'s one test runs in `bridge-replay`'s job
(`pytest -m crossrepo tests/app/test_canvas_app.py tests/crossrepo`, 12 tests with D4's forwarding). `cross-repo.yml`
schedules itself (`17 6 * * *`) and `v1-desktop` deletes `nightly.yml`. GitHub runs a schedule only from the default
branch, so until the stack merges `main`'s `nightly.yml` keeps dispatching `cross-repo.yml` on `v1-desktop`, and once
#42 merges the schedule runs on `main`. Without `has-d5`, a pull request whose tree holds the new `cross-repo.yml` but
no `desktop/pins.toml` would fail its jobs, so `pins.toml` lands first (#40, below #42). Decision M, §1.3, §7.5.

B27. **One table of exit codes beside `SetupError`, in `dr_app.layout`; `AppLayout.state_dir` gone** (as-built #15,
#25; `0f1d0e0`). The exit codes were defined in five modules; they are one table (2 and 10–14), each with what it
means, beside the `SetupError` that carries them, and the other modules import them. `AppLayout.state_dir` and
`STATE_DIRNAME`, which nothing read, are gone. `runtime.py` reads top-down. No behaviour changes. §4.3.2, §5.1,
§5.2, §5.6.

B28. **The default cap is defined once, in `acp/cli.py`; `Spend` is the ledger's own account** (as-built #25;
`440e1ac`). `proxy.DEFAULT_SPEND_CAP_USD` was read only by a test; `dr-acp`'s `cli.py` holds `DEFAULT_SPEND_CAP_USD =
5.0`. `dr_app.profile`'s `"5"` stays, since `dr_app` imports nothing of deep-reasoning's. `Spend` is each root
session's mutable account (spent, reserved, calls, refused), `SpendLedger.spend()` returns a copy, and the cap is
`SpendLedger.cap_usd`. The refusal's body is built in `KeyProxy._refuse`. No behaviour changes. §4.7.1, §5.7.

B29. **Shared clients and reading order** (as-built §8; `6ee106c`, `94683bd`, `9134faf`, `3e9cee9`). The two test
harnesses (`tests/crossrepo/agent_server.py`, `tests/desktop/app.py`) call the agent-server through
`dr_app.agent_server.AgentServer` instead of private copies; tests import `desktop.build` as a module; `build.py`
reads in order (the sentences, `check_pins`, the defaults, the forks' readers, the build, `verify`); `dr-app export`
reads the recorded home itself; `proxy.py`'s docstring maps its three parts. No behaviour changes. §5.8, §7.5.

**Size** (as-built #17; §3 item 15, §10). The spec costed D5 at ≈1.2k lines with tests and ≈4 h at Gate C; v2 at
≈1.45k of code and ≈1.24k of tests, ≈2.7k, about 9 h. Gate C reads **6,512 reviewable lines, 2,589 of code and 3,923
of tests**, and the README's 161 (non-blank lines added, level by level; the review ledger's count), about 22 h at
≈300 lines an hour. By `wc` (the as-built's count), D5's own files hold 2,913 lines of code, 339 of them workflows,
and 4,423 of tests, and D1's files gain 128 net lines of code and 114 of tests. The refactor took code from 2,644 to
2,579 and tests from 3,999 to 3,917 (the task row: 6,643 before, 6,496 after). Where v2 fell short: E12 and its
harness, 1,104 lines (`test_e12.py` 727, `app.py` 192, `e12/subagents.py` 106, `test_app.py` 79) against ≈280; setup's
tests, 1,504 lines with `fake_agent_server.py` and the stub tools, against ≈405; `dr_app` itself, 1,301 against ≈535;
the proxy and its tests, 1,338 with E10's 287, against ≈720; `build.py`, 532 against ≈250 for all of `desktop/`. The
build recorded no reason for the growth; the estimate was this design's.

**The stack** (#36–#44). Nine one-commit levels, bottom-up from `main` (`f1ca641`): the key proxy (#36), the grant
that puts it between the worker and every key (#37), setup's before-start (#38) and after-ready (#39), the SDK fork's
pin with what is checked against it (#40), the build (#41), `cross-repo.yml` and E12 (#42), the release (#43), the
README (#44). #40 sits below #41 because `tests/crossrepo/agent_server.py` reads `desktop/pins.toml` when imported,
and because `main`'s `cross-repo.yml` runs `library-app` and `bridge-replay` on any pull request whose tree has
`pins.toml`, so the level that adds the pin must hold the tests those jobs run (B26). The split adds no code of its
own: where a level holds part of a file it holds those lines of the final file, except that imports name fewer things,
docstrings and comments name only what their level holds, and config lists (ruff's paths, the pytest markers,
`pins.toml`'s tables, the stub tools) have fewer entries; in #38, `profile.py` holds only the default cap and `cli.py`
has no after-ready branch. #44's description lists each. The stack top's tree is `3e9cee9`'s less this file.

---

## 4 · Modules

### 4.1 Files in deep-reasoning

```text
desktop/
    pins.toml                      what one build is made of (§4.2.1)
    build.py                       the build: checks, defaults, frontend, packages (stdlib; `uv run desktop/build.py`)
    electron-builder.dr.mjs        the fork's electron-builder config under our name (§4.2.4)
    bootstrap.sh                   the setup command's sh wrapper, embedded into defaults.json (§4.3.1)
packages/dr-app/                   the deep-reasoning-app package (stdlib only; a uv workspace member)
    pyproject.toml                 requires-python ">=3.12,<3.13", script dr-app = "dr_app.cli:main"
    src/dr_app/
        __init__.py
        cli.py                     dr-app setup | export | home
        layout.py                  AppLayout, the data home, SetupState (setup.json)
        runtime.py                 RuntimeSpec, run_logged, the checks, install_runtime, runtime_is_current
        agent_server.py            AgentServer: a urllib client for the agent-server's REST API
        profile.py                 the deep_reasoner agent profile
        canvas_app.py              stage, install, approve and start the Library App (v2: skeleton)
        texts.py                   every user-visible sentence (§6)
        runtime.lock.txt           `uv export` of the root project's uv.lock (package data)
src/deep_reasoning/acp/
    proxy.py                       KeyProxy, ProxyRoute, SpendLedger (new)
    cli.py                         two options (D1's file)
    route.py, catalog.py, supervisor.py, worker/protocol.py, worker/runner.py   the seam extension (§8.1, D1's files)
    testing/fake_model.py          FakeCall gains the call's Authorization header (D1's test helper, §7.1)
tests/app/                         dr-app (§7.2)
tests/acp/test_key_proxy.py        the proxy's units; tests/acp/test_e10_keys.py  E10 (§7.1)
tests/canvas_app/test_notice.py    one line: texts.safety("7") (D3's file, decision O)
tests/desktop/                     build.py (§7.3); test_e12.py and e12/ (marker desktop, §7.5)
tests/crossrepo/                   E5's bridge replay (marker crossrepo; v2: skeleton)
.github/workflows/
    fork-live.yml                  S1's and S2's live tiers with dr-acp (§7.4; v2: built, on main)
    cross-repo.yml                 pins, E12, E5, E6 (§7.5)
    desktop-release.yml            per-OS builds (§7.6)
    nightly.yml                    on main only: dispatches cross-repo.yml (decision M)
```

Repository wiring, in `main`'s `pyproject.toml` (*v2:* re-read at `1f9fe52`): `[tool.uv.workspace] members =
["packages/dr-app"]`, `deep-reasoning-app` in the dev group with `[tool.uv.sources] deep-reasoning-app = {
workspace = true }`, so the tests import `dr_app`; `uv export --no-emit-workspace` keeps both workspace members out
of `runtime.lock.txt`. *(v2)* `httpx` moves from the dev group into `[project] dependencies`: the proxy imports it,
and today it reaches the runtime only as deep_reasoner's dependency (the lock already holds 0.28.1). Pytest's
`addopts` becomes `-m 'not live and not browser and not desktop and not crossrepo'` (D3 added `browser`), with
the two new markers declared. CI's ruff steps cover `src tests packages desktop`. The dev group already has
`playwright==1.56.0` (D3 added it; E12 drives the app over CDP with it). The hatch sdist already excludes `docs/`;
the dr-app wheel ships `runtime.lock.txt` as package data.

*(v3: the tree at `3e9cee9` differs from the listing above in these, and nothing else. `runtime.lock.txt` does not
exist, and the dr-app wheel ships no package data (B22). `.github/workflows/nightly.yml` is not D5's: it lives only on
`main`, from #34, and #42 deletes it (B26). New files: `README.md` at the root, which `pyproject.toml` names as its
`readme` (B18); `tests/app/fake_agent_server.py`, `test_texts.py` and `conftest.py`'s stub `uv`, `uvx` and `git`;
`tests/acp/test_texts.py`'s proxy test, `test_catalog.py`'s and `test_runner.py`'s seam tests in D1's files;
`tests/crossrepo/agent_server.py` (the SDK fork's agent-server, started from `DR_SDK_CHECKOUT`) and
`test_mcp_forwarding.py` (D4's, §8.7); `tests/desktop/app.py` (the launch harness E12 and the smoke share),
`test_app.py`, `e12/subagents.py` (C1's two DOM reads in Python), `test_launch_smoke.py` and `test_readme.py`. There
is no `tests/desktop/e12/main.yaml` (B7). `pyproject.toml` also gives ruff `src = [".", "src",
"packages/dr-app/src"]`, and `.gitignore` gains `.desktop-work/` and `/dist/`.)*

### 4.2 The build

#### 4.2.1 `desktop/pins.toml`

```toml
# What one desktop build is made of. A pin moves only when cross-repo.yml is green on the new set (spec §2).
# Commits are authoritative (Michael's ruling); tags are for people and for the TypeScript client check.

[canvas_fork]
repo = "https://github.com/michaeltheologitis/OpenHands"
commit = "<40 hex: the redone wiring's merge into deep-reasoning, §8.6>"
tag = "dr-1"

[sdk_fork]
repo = "https://github.com/michaeltheologitis/software-agent-sdk"
commit = "34c540ce0598b20ddf913d51968dd903c1c13b2e"
tag = "dr-2"

[app]
product_name = "Deep Reasoning"
app_id = "io.github.michaeltheologitis.deep-reasoning"
executable_name = "deep-reasoning"
version = "1.0.0-rc.1"
maintainer = "<name and email for the .deb; fpm requires an email>"
uv_version = "0.12.23"
```

*(v3: the values at `3e9cee9`: `[canvas_fork]` `4355a36580191bb98d53610152469864d9640b8a`, tag `dr-3`; `[sdk_fork]` as
above; `maintainer = "Michael Theologitis <michael.theologitis@outlook.com>"`, his ruling. The rest of `[app]` is as
above. The Canvas fork's tags are `dr-1` (`fc87687`), `dr-2` (`9d050ab`) and `dr-3`, numbered apart from the SDK
fork's, as below. B1.)*

*(v2)* The values are the skeleton's first set. The SDK fork's is `34c540c` with the tag Michael is pushing there
(`dr-1`, `cef3b24`, is on `dr/integration`, not `deep-reasoning`, so check 8 refuses it). The Canvas fork has no tag
yet: its first, `dr-1`, is cut at the redone wiring's merge (§8.6), and the two forks number their tags apart, as the
spec's mock-up does (its Canvas `dr-2` runs SDK `dr-3`), since a Canvas-only change (C1, C2) moves only the Canvas
tag. `uv_version` is the release C3's live test last proved the offline relaunch on, for the SDK fork's commit
(C3 v3 §9 item 6, run 37148193696); v1's 0.8.17 was the version C3 measured by hand (§11 item 15).

deep_reasoner's pin is not here: it is the root project's dependency (`pyproject.toml`, `uv.lock`) and so a
line of `runtime.lock.txt`. deep-reasoning's own commit is the checkout's `HEAD` at build time.

#### 4.2.2 The pin checks

`check_pins` runs before anything is built, in the build and as `cross-repo.yml`'s first job. Each failure is one
sentence (§6) and the build stops.

1. Each fork's tag resolves to its pinned commit (`git ls-remote <repo> refs/tags/<tag> refs/tags/<tag>^{}`;
   the peeled line wins for an annotated tag, C3 §2.3).
2. The Canvas checkout's `config/defaults.json` has `sources.agentServerGitRepo` equal to the SDK fork's repo and
   `sources.agentServerGitRef` equal to its commit (the Canvas fork's wiring commit, C3 §4.5; *v2:* the redone
   wiring, §8.6). This is the spec's "pins that do not belong together".
3. The Canvas checkout's `package.json` names `@openhands/typescript-client` by a URL containing
   `/releases/download/<sdk tag>/` (the tarball the SDK fork's release step publishes, Q2 (a)).
4. The SDK fork's `uv.lock` at its commit locks the same `agent-client-protocol` version as ours (spec §2: one
   ACP Python at both ends).
5. The Canvas checkout's `paths.stateDir` and `setup` are `null`: the fork carries no value of ours.
6. The deep-reasoning checkout is clean and its `HEAD` is on `origin` (`git branch -r --contains HEAD`), because
   every user's setup will fetch that commit.
7. `runtime.lock.txt` equals `uv export` of `uv.lock` (§7.2's test, run here too).
8. *(v2)* Each fork's pinned commit is on that fork's `deep-reasoning` branch: the history of
   `refs/heads/deep-reasoning`, fetched without blobs (`git fetch --filter=blob:none <repo> deep-reasoning`) into a
   cache under `--work`, contains it (`git merge-base --is-ancestor <commit> FETCH_HEAD`). The fork stacks merge
   into `deep-reasoning`, and the spec pins a `dr-N` tag there; a tag cut on another branch (`dr-1`, on
   `dr/integration`) would ship code no stack carried.

*(v3: seven checks, as built (B24, B22). 1 and 3 as above. 2 is two sentences, one for the repository
(`wired_to_another_repo`) and one for the commit (`wired_elsewhere`, §6's). 4 reads the SDK fork's `uv.lock` at its
commit from `raw.githubusercontent.com`. 5 asks only that `paths.stateDir` and `setup.command` be null: the fork sets
`setup.phases`. 6 as above. 7 is gone, with the exported lock it compared. 8 asks GitHub's compare API,
`repos/<fork>/compare/<commit>...deep-reasoning`: `ahead` or `identical` passes, any other status or a 404 refuses;
`GITHUB_TOKEN`, when set, authenticates. Nothing is cached under `--work` but the Canvas checkout. `check_pins` takes
the readers as arguments, so the tests run every check without a network; `build.py check` passes the real ones,
and so does the `pins` job.)*

#### 4.2.3 What the build writes into the Canvas checkout

`config/defaults.json`, after the checks, and nothing else in the checkout:

| Key | Value |
|---|---|
| `paths.stateDir` | `"~/.deep-reasoning/canvas/agent-canvas"` |
| `setup.command` | `["sh", "-c", <bootstrap.sh, verbatim>, "dr-app-bootstrap", "git+https://github.com/michaeltheologitis/deep-reasoning@<commit>#subdirectory=packages/dr-app", "https://github.com/michaeltheologitis/deep-reasoning", "<commit>"]` |
| `setup.phases` | `["before-start", "after-ready"]` |
| `telemetry.posthogApiKey` | `""` |

The file is compiled into the frontend (C3 §4.1), so it holds nothing secret: a script, a URL and a commit.
*(v3: built so; `test_defaults_gain_only_d5s_four_keys` pins it.)*

#### 4.2.4 The packages

In the Canvas checkout, in order:

1. `npm ci` (the wiring commit's tarball URL brings our TypeScript client: *v2:* release `dr-2`'s, §8.6).
2. `VITE_DO_NOT_TRACK=1 npm run build:app`.
3. `UV_VERSION=<pins.app.uv_version> node scripts/download-uv.mjs` and `node scripts/download-node.mjs`, with
   `ELECTRON_ARCH=universal` for the macOS release, and `GITHUB_TOKEN` for the API lookup as upstream's workflows
   pass it.
4. `npx electron-builder --config <repo>/desktop/electron-builder.dr.mjs --projectDir <checkout> --publish never`
   (plus `--linux` or `--mac`), with `DR_CANVAS_DIR` and the `[app]` values in the environment.
5. Check the output: exactly the expected artifacts, named `deep-reasoning-<version>-<arch>.<ext>`; for the
   `.deb` and `.AppImage`, list the payload and fail if any path contains `deep_reasoner` (§2.1).

*(v3, B14, B19: the targets are `linux` and `mac-arm64`, and each refuses to run on any machine but its own (Linux
x86-64, macOS arm64; `wrong_machine`), because the fork downloads uv and Node for the machine it builds on:
`ELECTRON_ARCH` is unset, not `universal`. Before step 1 the build checks the pins (§4.2.2) and writes the defaults
(§4.2.3). Step 5's `verify()` also requires, for the Mac, one `deep-reasoning-<version>-arm64.dmg`, `lipo -archs` =
`arm64` for the `.app`'s Electron, uv and Node (`not_arm64`), and `Info.plist`'s `LSMinimumSystemVersion` = `14.0`
(`opens_too_early`); a `.deb`'s payload is its `dpkg-deb -c` listing, spaces kept. Then the artifacts are copied to
`<repo>/dist/`.)*

`desktop/electron-builder.dr.mjs`, whole (*v3:* as built, with its `mac` line, B19):

```js
// The Canvas fork's electron-builder config under our name. No fork commit: the build points --config here.
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const env = process.env;
const fork = await import(pathToFileURL(join(env.DR_CANVAS_DIR, "electron-builder.config.mjs")).href);
const base = fork.default;
const productName = env.DR_APP_PRODUCT_NAME;
const executableName = env.DR_APP_EXECUTABLE_NAME;
const version = env.DR_APP_VERSION;
const artifactName = executableName + "-${version}-${arch}.${ext}"; // electron-builder macros, not JS

export default {
  ...base,
  appId: env.DR_APP_ID,
  productName,
  extraMetadata: { ...base.extraMetadata, name: executableName, productName, version },
  // The oldest macOS the runtime's arm64 wheels install on: macOS refuses to open the app on an older one.
  mac: { ...base.mac, minimumSystemVersion: "14.0" },
  dmg: { ...base.dmg, title: productName, artifactName },
  linux: { ...base.linux, executableName, artifactName, maintainer: env.DR_APP_MAINTAINER },
  win: undefined,
  nsis: undefined,
};
```

Relative paths in the fork's config (`directories.app`, `extraResources`) resolve against `--projectDir`, and its
`afterPack` hook finds the checkout from its own module path, so both work unchanged.

#### 4.2.5 What stays upstream's in the app

Strings hard-coded in the fork's Electron code keep upstream's name: the splash banner (`bannerTitle`,
`electron/main.mjs:664`), the startup-failure dialog's title (`:755`) and the missing-`uv` dialog (`:708`); the
first-launch notice still says it installs the agent-server "from PyPI" (`:681`), which our build does from git. The
icon stays upstream's (§11 item 6). The menu, the dock, the window list and `userData` take our product name. *(v3:
the macOS launch log shows upstream's "OpenHands Agent Canvas (Static)" banner; the rest is not checked, as-built §7.
The name a user reads is TASK-44's, in the later UX round, B17.)*

#### 4.2.6 Signing

None, as the spec decided: upstream's macOS builds are ad hoc signed by electron-builder and its Linux packages
unsigned (`.github/workflows/desktop-*.yml`). The README gives the macOS command after copying the app to
Applications: `xattr -dr com.apple.quarantine "/Applications/Deep Reasoning.app"`.

### 4.3 The setup command

#### 4.3.1 `desktop/bootstrap.sh`

Run by C3's launcher as `sh -c <script> dr-app-bootstrap SPEC REPO COMMIT`, with stdin closed and every line in
the startup log (C3 §4.2), so it prints nothing secret. Whole (*v3:* as built; the fetch line no longer asks for read
access, since deep-reasoning is public, B15):

```sh
# The setup command (C3 §4.2): explain the two failures that happen before dr-app exists, then run it.
set -u
export GIT_TERMINAL_PROMPT=0
: "${GIT_SSH_COMMAND:=ssh -o BatchMode=yes}"
export GIT_SSH_COMMAND
case "$(uname -s)" in Darwin) PATH="$PATH:/opt/homebrew/bin:/usr/local/bin" ;; esac
if ! git --version >/dev/null 2>&1; then
  echo "✗ deep_reasoner is fetched with git, which was not found. On macOS run xcode-select --install; on Linux install git."
  exit 10
fi
uvx --from "$1" dr-app setup --repo "$2" --commit "$3"
status=$?
if [ "$status" -ne 0 ] && { [ "$status" -lt 10 ] || [ "$status" -gt 19 ]; } && ! git ls-remote "$2" HEAD >/dev/null 2>&1; then
  echo "✗ Could not fetch ${2#https://}: check that this computer is online, then restart. Nothing was installed."
fi
exit "$status"
```

- `GIT_TERMINAL_PROMPT=0` and SSH's batch mode keep git from prompting on a terminal (C3 §4.6); a run from Finder
  has no terminal anyway. The two Homebrew directories go at the end of `PATH` because a credential helper
  configured by bare name (`git-credential-manager`, `gh`) is not on a Finder-launched app's `PATH` (C3 §4.2).
- `dr-app` exits 0, or 10–19 after saying why (§5.2). Any other status means `uvx` failed before `dr-app` ran (or
  argparse refused its arguments); then, and only then, the bootstrap asks git whether the repository is
  readable. A relaunch never reaches that line: `uvx` starts from its cache.
- On macOS with no Command Line Tools, `/usr/bin/git --version` fails and opens Apple's install dialog, which is
  what the message tells the user to do.
- *(v2, C3 v3 §4.2)* `sh` is the command the launcher spawned, so it leads the process group, and `uvx` and
  `dr-app` stay in it: a timeout or a quit signals all three, even after `sh` itself has exited. Nothing here
  detaches. `uvx`'s own fetch of `dr-app` (a first launch, an update) inherits the launcher's output; a git
  credential helper that daemonizes while keeping it would hold the phase open (§11 item 14). Everything `dr-app`
  starts is on a pipe of its own (decision P).

#### 4.3.2 `dr-app setup`

`dr-app setup [--phase before-start|after-ready] --repo URL --commit SHA`. The phase defaults to
`$OH_CANVAS_SETUP_PHASE` (C3 §4.2); with neither, it runs before-start, then after-ready if `AGENT_SERVER_URL` is set
(a run by hand). The whole command holds an exclusive lock on `~/.deep-reasoning/setup.lock` (`fcntl.flock`), so a
terminal run and a launch cannot interleave. Every line goes to stdout, flushed; nothing prints `SESSION_API_KEY`, a
token, a key or a credential. Exit codes: 0; 10 a check failed; 11 the runtime install failed; 12 the agent-server
refused a call setup depends on; 13 the data home is unusable; 2 usage. *(v3: one table in `dr_app.layout`, beside
`SetupError`, B27: 2 also covers after-ready without `AGENT_SERVER_URL` and `SESSION_API_KEY` (`NO_AGENT_SERVER`); 13
also a home too long for a Claude run's socket (B3) and `export` with nothing installed; and **14**, a `setup.json`
this app cannot use (B21). `export` takes no lock; `setup` and `home` do.)*

*(v2, decision P)* Every subprocess runs through `run_logged` (§5.2): its stdout and stderr on one pipe that
`dr-app` reads, each line copied to stdout as it comes, and the call returns at the subprocess's exit, whatever still
holds the pipe. So when `dr-app` exits, nothing it started keeps the launcher's output, and the phase ends as
`uvx` and `sh` return. A quit
mid-phase stops the whole group within about 4 s (C3 v3 §4.4); a phase still running at 15 minutes (a slow first
install) is stopped the same way and fails the launch with C3's timeout message. Either way the next launch finds a
`*.tmp-*` runtime to remove, the lock released with the process that held it, and `setup.json` as last saved, so it
simply installs again, with whatever uv already downloaded still in its cache.

### 4.4 before-start

1. Create `~/.deep-reasoning` (0700) and load `setup.json` (absent: a fresh `SetupState`).
2. Choose the data home (§4.4.1); when it differs from the recorded one, say so (`home_local` or `home_network`)
   and record it.
3. `spec = RuntimeSpec.for_commit(repo, commit)`. If `runtime_is_current(layout, state.runtime, spec)`, go to 6.
4. The checks (§4.4.2), then `checks_ok`; on a first install (`state.runtime is None`) the `safety` line; then
   `installing`.
5. `install_runtime` (§4.4.3); `installed`; record it.
6. Make `~/.deep-reasoning/bin/dr-app` and `bin/dr` links to `runtime/current/bin/` if missing.
7. *(v2: removed. v1's fallback that wrote the ingress into the agent-server's config file is not needed: C3's
   launcher sets it, §4.9. The number stays so that nothing citing step 8 moves.)*
8. Save `setup.json` (temporary file, then rename).

*(v3, B22 and B23: steps 3 to 5 as built. 3: the commit must be 40 hex; if `runtime_is_current(layout,
state.runtime, commit)`, go to 6. 4: `git --version` (`NO_GIT`), `uv` on `PATH` (`NO_UV`), then, inside
`fetched_source`, the commit's tree fetched into `runtime/`; deep_reasoner's URL and commit from that tree's
`uv.lock` (`deep_reasoner_pin`); deep_reasoner readable (`no_access_dr`); then `checks_ok`, on a first install the
`safety` line, and `installing`. 5: `install_runtime` from that tree; the tree is removed; `installed`. A
`setup.json` this app cannot use stops step 1 with exit 14, B21.)*

`runtime_is_current` is true when the record's commit and lock digest equal the spec's, `runtime/current`
resolves to the record's path, and `<path>/bin/python -I -c ""` exits 0 (one exec, about 20 ms: it catches a
deleted runtime and a removed managed Python). So a relaunch with nothing changed costs one JSON read, a few
`stat`s and that exec, plus `uvx`'s own start. *(v3: the record's commit alone, which fixes its `uv.lock`, B22. A
relaunch's before-start took 0.02 s, and the whole bootstrap 0.12 s warm, with or without a network, as-built §5.5.)*

#### 4.4.1 The data home

`choose_home` takes the first that applies:

1. **A recorded home** (`setup.json`'s `dr_home`, written by an earlier launch or by `dr-app home`) that still
   exists, is a directory owned by the user, and is not on a network filesystem: keep it.
2. **`~/.deep-reasoning`,** unless (Linux only) its filesystem type is one of D2's `NETWORK_FILESYSTEMS`, read from
   `/proc/self/mounts` (the longest mount point that prefixes the resolved path), exactly as D2's store does
   (D2 §4.2). `dr_app` mirrors D2's set, and a test pins that the two are equal (§7.2).
3. **`/var/tmp/deep-reasoning-<uid>`** (Linux, on a network home): created with mode 0700 if absent. If it
   exists, `lstat` must show a real directory (not a link) owned by the user with no group or other permissions;
   otherwise exit 13 with `home_unsafe`, because `/var/tmp` is shared and another user could have made it first.

macOS homes are local and get no check (as in D2). `home_network` says that systemd may delete files in
`/var/tmp` unused for 30 days, and how to export or move the data. Nothing is ever moved by setup.

*(v3, B3: and a fourth rule, after the choice: the home must leave room for a Claude run's socket.
`check_socket_room` refuses, exit 13 with `home_too_long`, a home under which `runs/<run id>/children/<n>/repl.sock`
(the home plus 52 bytes, `DEEPEST_SOCKET`) is longer than the system lets a socket bind: 107 bytes on Linux, 103 on
macOS (`SOCKET_PATH_MAX`). `dr-app home DIR` applies the same rule. A recorded home that is no longer a directory of
the user's falls through to rule 2.)*

#### 4.4.2 The checks

Run only when the runtime must be installed, so an offline relaunch never runs them:

- `git --version` (the bootstrap already checked; `dr-app` reports the version in `checks_ok`).
- deep_reasoner is readable: `git ls-remote <url> HEAD`, with the bootstrap's git environment, where `<url>` is
  parsed from `runtime.lock.txt`'s `deep-reasoner @ git+<url>@<commit>` line. On failure: `no_access_dr`, exit 10.
  This is the spec's "Nothing was installed": it runs before any install step.
- `uv` is on `PATH` (the app's bundled one comes first): otherwise `NO_UV`, exit 10.

deep-reasoning's own readability needs no check: `dr-app` is running, so `uvx` fetched it.

*(v3, B22 and B23: the order is git, `uv`, then the fetch of deep-reasoning's tree at the commit, then deep_reasoner's
readability, whose `<url>` is read from that tree's `uv.lock` (the `deep-reasoner` package's `source.git`), since
there is no packaged lock. `git ls-remote`'s output goes nowhere, so a credential helper left behind holds no pipe. A
failed fetch is `install_failed` naming `git fetch`, exit 11, not a check: offline with no current runtime, a user now
sees that rather than `no_access_dr`, B23. Nothing is installed either way.)*

#### 4.4.3 The runtime install

```text
remove runtime/*.tmp-* left by an interrupted install
uv venv --managed-python --python 3.12 runtime/<commit>.tmp-<pid>
uv pip sync --python runtime/<commit>.tmp-<pid>/bin/python <requirements>
    <requirements> = runtime.lock.txt
                   + "deep-reasoning @ git+<repo>@<commit>"
                   + "deep-reasoning-app @ git+<repo>@<commit>#subdirectory=packages/dr-app"
runtime/<commit>.tmp-<pid>/bin/python -c "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
rename runtime/<commit>.tmp-<pid> → runtime/<commit>     (an existing runtime/<commit> is removed first)
link runtime/current.tmp → <commit>; rename over runtime/current
remove every other runtime/<…>
```

*(v3, B22 and B2: as built, from `3e9cee9`'s `runtime.py`:*

```text
remove runtime/*.tmp-* left by an interrupted install
git init -q runtime/<commit>.tmp-<pid>-source                                 (fetched_source, each step run_logged)
git fetch -q --depth 1 <repo> <commit>; git checkout -q FETCH_HEAD             (in that tree)
deep_reasoner_pin: deep_reasoner's URL and commit from the tree's uv.lock; the readability check (§4.4.2)
uv venv --relocatable --managed-python --python 3.12 runtime/<commit>.tmp-<pid>
UV_PROJECT_ENVIRONMENT=runtime/<commit>.tmp-<pid> uv sync --frozen --no-dev --no-editable --all-packages --project <tree>
runtime/<commit>.tmp-<pid>/bin/python -c "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
rename runtime/<commit>.tmp-<pid> → runtime/<commit>     (an existing runtime/<commit> is removed first)
link runtime/current.tmp → <commit>; rename over runtime/current
remove every other runtime/<…>, then the tree
```

*`--all-packages` installs both workspace members, deep-reasoning and deep-reasoning-app, from the tree, not
editable; `--frozen` takes `uv.lock` as it is. The record keeps the commit and, unread, the lock's digest. A step that
exits non-zero is `install_failed` naming it (`git init`, `git fetch`, `git checkout`, `uv venv`, `uv sync` or `the
import check`). Measured with the bundled uv 0.12.23: 7 s from a cold cache, the managed Python included; 173
packages; a 474 MB runtime (as-built §5.4). The paragraph below is v2's.)*

`uv pip sync` installs exactly the listed set and nothing it resolves itself; the export carries every transitive
dependency with platform markers, so one file serves macOS and Linux. The two git lines are built from source by
hatchling (fetched from PyPI the first time; cached after); deep-reasoning's wheel carries D3's committed App files as
package data. Every subprocess gets the bootstrap's git environment and runs through `run_logged`, so its output
streams into the startup log and nothing it leaves behind holds the phase (decision P). A non-zero exit is
`install_failed`, exit 11; `current` still points at the previous runtime, but the launch stops (an app update tested
its pins together, so an older `dr-acp` with newer forks is not a state to run in). The spec's mock-up measured the
first install at about two minutes; C3's 15-minute limit per phase bounds it.

### 4.5 after-ready

`AGENT_SERVER_URL` and `SESSION_API_KEY` come from the launcher (C3 §4.2). Every call sends the key as
`X-Session-API-Key` through a `urllib` opener with `ProxyHandler({})`, because on macOS Python would otherwise
send loopback traffic to a system HTTP proxy (S2 decision G).

1. **The agent profile** (§4.5.1). A failure is `agent_server_failed`, exit 12.
2. **The model-key hint.** `GET /api/settings/secrets` lists names; if none is `OPENAI_API_KEY` (the starter
   Library's key, D2 decision M) and none other than `OPENHANDS_AUTOMATION_API_KEY` ends in `_API_KEY`, print
   `NO_MODEL_KEY`. Never fails the launch.
3. **The Library App** (§4.6; *v2:* skeleton). Never fails the launch.
4. Save `setup.json`.

#### 4.5.1 The `deep_reasoner` agent profile

Canvas starts a conversation from the active agent profile (`use-create-conversation.ts:121`), so the profile is
how `dr-acp` becomes the app's agent. `ensure_profile`:

1. `existing` = the `profile` of `GET /api/agent-profiles/deep_reasoner` (404: none).
2. `want = desired_profile(existing, dr_acp=~/.deep-reasoning/runtime/current/bin/dr-acp, home=DR_HOME)`:

   | Field | Created as | On a later launch |
   |---|---|---|
   | `agent_kind` | `"acp"` | owned: reset |
   | `acp_server` | `"custom"` | owned: reset |
   | `acp_command` | `shlex.join([dr_acp])` (the resolver splits it with `shlex`, `profiles/resolver.py:286`; macOS paths can hold spaces) | owned: reset |
   | `acp_subagents` | `true` (S1 §4.6, guarantee 8; merged, §8.2) | owned: reset |
   | `acp_args` | `["--home", DR_HOME, "--spend-cap-usd", "5"]`, each a separate entry (D3 reads the cap from them, D3 §8.4 item 5) | the `--home` pair is owned (replaced or inserted at the front); every other argument is kept |
   | `secret_refs` | `null`: all of the user's secrets (§2.2) | kept |
   | `mcp_server_refs` | `null`: all servers; D4 grants per namespace, and relies on this (D4 §11.4) | kept |
   | everything else | the model's defaults | kept |

3. If `existing` is absent or differs from `want` in an owned field: `POST /api/agent-profiles/deep_reasoner`
   with `want` (the server keeps the profile's `id` and bumps its `revision`, `agent_profiles_router.py:307–364`).
   *(v2: v1's fallback for a 422 naming `acp_subagents` is gone. Every pin the build accepts carries S1's profile
   field (`profiles/agent_profile.py:292`), so a 422 is an agent-server refusing what setup depends on:
   `agent_server_failed`, exit 12.)*
4. Find its `id` in `GET /api/agent-profiles` (listing also triggers upstream's one-time seeding of a default
   profile on an empty store, `agent_profiles_router.py:256–282`, so ours is activated after it).
5. If `setup.json` does not record that setup activated it before: `POST /api/agent-profiles/{id}/activate` and
   record it. A profile the user deleted is created again on the next launch, but not made the default again.

*(v3, B25: steps 3 and 4 as built. `needs_write` compares the owned fields and `acp_args`, which differ only when the
`--home` pair moved, since every other argument is kept. After a write, setup reads `GET
/api/agent-profiles/deep_reasoner` again for the id the server kept or minted; without a write, the first GET's id.
Setup never lists the profiles: upstream's seeding needs an empty store, and setup has written ours before any listing
could see one. `PROFILE_CREATED` is printed when setup activates, `PROFILE_UPDATED` when it only writes. In the app,
Canvas `dr-3`'s onboarding offers the active profile first and keeps it (#29), so a first launch keeps
`deep_reasoner` the default, and E12 pins that onboarding writes no profile.)*

### 4.6 The Library App

*(v2: skeleton; v1's final part. D3 and S2 are merged, and D3 §8.4 settled the split below.)* D3 builds the App and
ships its built files in the deep-reasoning wheel, under `deep_reasoning/canvas_app/`: `canvas-extension.json`
(name `dr-library`, `version` the package's, `0.1.0`; `entrypoint` `dist/index.js`; one conversation panel,
`decompositions`, icon `panel.svg`, four tabs; no `backend` block), `dist/index.js`, `panel.svg`, and `ui/`, which
`dr-library serve` serves at `/ui/` from the same runtime. D5 adds the backend and installs it.

1. **Find D3's files** in the runtime: `runtime/current/bin/python -c` printing
   `importlib.resources.files("deep_reasoning.canvas_app")`. Of them D5 stages exactly three, `STAGED_FILES`:
   `canvas-extension.json`, `dist/index.js` and `panel.svg`. Not `ui/`: a UI-only change must not change the
   digest, which would force a reinstall that stops the backend (D3 §8.4 item 1).
2. **Make the backend artifact**, deterministically (same bytes for the same home, so the same checksum and no
   new approval across launches and upgrades): a gzip (`mtime=0`) tar holding one member `bin/dr-library`, mode
   0755, owner 0, `mtime` 0, whose text is

   ```sh
   #!/bin/sh
   exec '<~/.deep-reasoning/runtime/current/bin/dr-library, shlex-quoted>' "$@"
   ```

   The agent-server checks that the resolved `argv[0]` is an executable regular file inside the unpacked artifact
   (`backend.py:395–412`; the manifest, that `argv[0]` names `{artifact_dir}`, `manifest.py:254–255`); the script
   is, and what it `exec`s is outside, which nothing checks. A `/bin/sh`
   script needs no code signature on Apple silicon (S2 §6.2).
3. **Write the manifest:** D3's `canvas-extension.json` (name `dr-library`) with a `backend` block:

   ```json
   {"schema_version": 1,
    "artifacts": {"<os>-amd64": {"path": "backend/dr-library.tar.gz", "sha256": "<hex>"},
                  "<os>-arm64": {"path": "backend/dr-library.tar.gz", "sha256": "<hex>"}},
    "argv": ["{artifact_dir}/bin/dr-library", "serve", "--port", "{port}", "--home", "<DR_HOME>"],
    "inherit_environment": ["LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ"]}
   ```

   `<os>` is `linux` or `darwin` (`darwin-*` since S2's #3); both architectures name the same script, which runs on
   either. The home is a literal because the backend gets no `DR_HOME` or `HOME` (D2 §4.8). `/health` is the default
   probe and D2's. `inherit_environment` is exactly the agent-server's allowed six (`backend.py:38–40`), which D4's
   Check also passes on to its child (D4 §3.3, `check_env`).
4. **Stage** the three files, the artifact and the manifest under `~/.deep-reasoning/canvas-app/<digest>/`, where
   `<digest>` is the SHA-256 over the manifest and every staged file's path and bytes; an existing directory of
   that name is reused.
5. **Install and start** (`ensure_canvas_app`):

   ```text
   info = GET /api/canvas-extensions/installed/dr-library           (404: none)
   if info is none or state.canvas_app.digest != staged.digest:
       if info: POST …/dr-library/backend/stop                      (a forced install refuses while any App's backend runs)
       POST /api/canvas-extensions/install {"source": <staged dir>, "force": info is not none}
       if info is none: PATCH …/dr-library {"enabled": true}        (a forced reinstall keeps the user's choice)
       record the digest
   if not enabled: print APP_DISABLED; stop here
   status = GET …/dr-library/backend
   unsupported → print APP_UNSUPPORTED; stop here                   (a platform no artifact names)
   if status.prepared_revision != status.revision: POST …/backend/prepare {"revision": status.revision}
   if status.state != "ready": status = POST …/backend/start {"revision": status.revision}
   ready → app_ready, else app_warning with the agent-server's detail
   ```

   *(v3: as built, with two details. An install is also forced when `setup.json` has no record of one, so a lost
   `setup.json` reinstalls rather than trusting what is there. `<digest>` is the SHA-256 over each staged file's path,
   a NUL and the SHA-256 of its bytes, in the order manifest, `dist/index.js`, `panel.svg`, the artifact.)*

   Installed from a local path, the App's revision is the hash of its manifest (`backend.py:151–159`), so it
   changes only when the manifest does. Each failing call prints `app_warning` and setup still exits 0. *(v2)* A
   forced install is refused while **any** App's backend runs (`canvas_extensions_router.py:209–212`,
   `has_running_backends`). At after-ready none runs, since backends do not survive an agent-server restart, so the
   `stop` matters only for a hand run; another App's backend still running then gives `app_warning`.

   *(v2)* After launch, D3's page keeps the backend up: before every mount it reads the status and, for a backend
   that is stopped or unhealthy with its revision prepared, calls `start`; it never calls `prepare` (D3 decision F,
   D3 as-built §3.2). Approving stays setup's alone.

Setup approving its own App's backend is the spec's call (D5's evidence: "installing this app is the user's
choice to run it"); the Apps page lists it like any other, and the user can disable it there.

### 4.7 The key proxy and the spend cap

#### 4.7.1 Where it sits

`dr-acp`'s front gains two options (D1's `cli.py`): `--spend-cap-usd USD` (default 5.0, per conversation) and
`--no-key-proxy` (D1's `DirectRoute`, for debugging). With the proxy, `main()` builds a `SpendLedger` and a
`KeyProxy` over the same `PriceTable` the encoder uses, and passes `ProxyRoute(proxy, os.environ)` to
`DrAcpAgent` as its route. The proxy's thread starts on the first grant, so a preview session (S2) that never
prompts never starts it. At shutdown `main()` stops it with a 0.5 s budget inside D1's 1.4 s (D1 §4.2). *(v3: as
built, B28: the default, `DEFAULT_SPEND_CAP_USD = 5.0`, and `PROXY_STOP_S = 0.5` are `acp/cli.py`'s, and the stop is
in a `finally` around `serve()`. A grant that holds no key and no `ANTHROPIC_API_KEY` is empty and does not start the
proxy either.)*

Each run, D1's `RunHandle.start` (`supervisor.py:133–143`) calls `route.grant(session=…, run=…,
upstream=source.client, tool_upstreams=source.tool_clients)` (the extension of §8.1), spawns the worker with
`worker_env(os.environ, grant)`, sends the overrides in `Start`, and calls `route.release(run)` when the run ends
(`supervisor.py:228`). The proxy forwards with `httpx`, a direct dependency from v2 on (§4.1).

#### 4.7.2 A grant

`ProxyRoute.grant`, for one run:

1. **The clients.** `"client"` (the main client) and `"tools.<name>.client"` for each tool block with its own
   client. For each: its key name is `api_key_env`, else deep_reasoner's default `NOVITA_API_KEY`
   (`config.py:95`); if `dr-acp` has no value for it but has `OPENAI_API_KEY`, the key is that one, as
   deep_reasoner's `build_client` would fall back (`config.py:256`). No value at all: the client is left as
   configured (nothing to protect; a keyless local server keeps working). Its upstream is `base_url`, else
   `$OPENAI_BASE_URL`, else `https://api.openai.com/v1`.
2. **Tokens and routes.** One token (`secrets.token_urlsafe(32)`) per key name held in this run; one route per
   distinct (upstream, key name), dialect `openai`, bound to that token. The client's overrides are
   `{"base_url": route.url, "api_key_env": <key name>}`.
3. **The Claude CLI.** If `dr-acp` holds `ANTHROPIC_API_KEY`, one more token and a route of dialect `anthropic`
   to `$ANTHROPIC_BASE_URL` or `https://api.anthropic.com`; the worker gets `ANTHROPIC_API_KEY=<token>` and
   `ANTHROPIC_BASE_URL=<route url>`, which a Claude-backbone agent's `claude` process inherits
   (`v2/claude_code.py:285–307`). Not verified against the real CLI (§11 item 3).
4. **The environment.** `env_add` maps each held key name to its token. `env_remove` is every variable whose value
   contains a held key, or the value of a variable that one of D1's `ALWAYS_REMOVED` patterns matches (values of at
   least 16 characters, so short accidental matches cannot remove `PATH`). *(v2: D1's `worker_env` already removes
   the `ALWAYS_REMOVED` names themselves, four glob patterns with `OPENHANDS_AUTOMATION_API_KEY` among them (D1 B2),
   so v1's `AGENT_SERVER_SECRETS` is gone; the proxy adds the copies under other names.)* `worker_env` removes, then
   adds, so each key's own name comes back holding the token.
5. **Loopback past system proxies.** `NO_PROXY` gains `127.0.0.1,localhost,::1`. On macOS, when the environment
   names no proxy but the system does (`urllib.request.getproxies()`), the system's HTTP and HTTPS proxies are
   exported as `HTTP_PROXY` and `HTTPS_PROXY` too: Python reads system proxies only when the environment names
   none, so `NO_PROXY` alone would switch them off for everything else the worker does (S2 decision G found the
   loopback half of this bug).

`release(run)` drops the run's routes and tokens; calls already in flight finish. A route's URL is
`http://127.0.0.1:<port>/r/<route id>`; route ids are 16 hex characters and appear only in that URL.

#### 4.7.3 A request

```text
POST /r/<route>/<rest>        (any other method on a metered path, or any other path: 403 not_a_model_call)
  route unknown, or the token (Authorization: Bearer … | x-api-key: …) not the route's → 401, nothing forwarded
  <rest> metered?   openai: chat/completions, completions, embeddings · anthropic: v1/messages
          free?     anthropic: v1/messages/count_tokens            → forwarded, not counted
  body: JSON, at most 32 MiB; model = body["model"]
  price unknown (estimate(model, {prompt_tokens: 1, completion_tokens: 1}).usd is None) and upstream not loopback → 400 unpriced
  stream requested (openai): body.stream_options.include_usage = true
  reserve = estimate(model, prompt_tokens = ceil(len(body) / 4),
                            completion_tokens = max_completion_tokens | max_tokens | 4096; 0 for embeddings)
  ledger.reserve(session, reserve) refuses → 402 cap_reached, in the dialect's error shape
  forward: the real key (Authorization: Bearer for openai, x-api-key for anthropic), the client's other headers
           minus hop-by-hop, Host, Cookie, Content-Length; httpx, trust_env off for a loopback upstream
  response: status passed through
     JSON  → usage = body.usage; a non-2xx body has every occurrence of the key replaced by "[redacted]"
     SSE   → streamed through as it arrives; usage read from the last openai chunk, or from anthropic's
             message_start (input) and message_delta (output)
  settle(reservation, estimate(model, usage).usd)     no usage reported: the reservation stands
                                                      upstream unreachable: 502 upstream_unreachable, settle 0
```

*(v3, as built. B5: a body that is not a JSON object of at most 32 MiB is 400 `bad_body`, before any price check;
`Accept-Encoding` is not forwarded and `Content-Encoding` not returned, and the client's `Authorization` and
`x-api-key` never travel. B4, Michael's ruling, changes `settle`'s second line: usage reported at any status is
charged; no usage on a 2xx keeps the reservation; **no usage on a non-2xx settles at 0**, the reservation released.
The order of refusals is 401, then 403, then `bad_body`, then (metered paths only) `unpriced`, then 402. A non-2xx
event stream is read whole, not relayed. One `threading.Lock` guards the ledger and another the routes, B28; the
ledger's file is rewritten after each settle and each refusal.)*

The price is the provider's when the response reports one, otherwise the table's (D1's `PriceTable`: the package's
`prices.yaml` under `$DR_HOME/prices.yaml`), and 0 for an unpriced model on a loopback upstream. Anthropic's cache
tokens are counted as input tokens. A 402 is not retried by the OpenAI client (it retries 408, 409, 429 and 5xx)
nor, as far as known, by the Claude CLI, so the agent fails at once and D1 shows the sentence as the failure's
detail. The proxy logs one line per refusal (reason, model, session) and never a header, a key or a token.

**The ledger.** Per root session: `spent_usd`, `reserved_usd` (in flight), `calls`, `refused`, and the cap in
force. `reserve` refuses when `spent + reserved + estimate > cap`. `settle` replaces the reservation by the cost.
After each settle the session's file `$DR_HOME/spend/<session>.json` is rewritten (temporary file, then rename);
a session's first reservation reads it, so a restarted `dr-acp` continues the count (the bridge reloads the same
session id, D1 §5.7). The overshoot is bounded by how far each call's real cost exceeds its reservation.

**Threads.** The server is `uvicorn.Server(Config(app, log_level="warning", lifespan="off"))` serving a socket the
caller bound to `127.0.0.1:0`, so the port is known before the thread starts. Routes and the ledger are shared
between the front's loop thread (grants, releases) and the proxy's thread (requests), under one
`threading.Lock`.

### 4.8 Export, the data home, and leaving

#### 4.8.1 `dr-app export DIR [--namespace NAME]`

Runs `runtime/current/bin/dr-library export DIR --home <DR_HOME>` (D2 §4.8), passing its output and exit code
through: `wrote DIR/main.yaml: 4 namespaces, 6 decompositions, 1 tool`. The result runs under `dr` unchanged
(E7 is D2's proof). With no runtime installed: `NOTHING_INSTALLED`, exit 13. It works while the app runs (WAL,
D2 §5.4).

#### 4.8.2 `dr-app home [DIR]`

Without `DIR`: prints the data home and, on Linux, its filesystem type. With `DIR`: it must be absolute, on a
local filesystem, and a directory the user owns (created 0700 if absent); setup records it, and the next launch
updates the profile's `--home` and the App's manifest (a new approval, which setup gives). Nothing is moved:
`home_set` says what to copy. *(v3: a relative path or a network filesystem is `home_refused`, and a path too long
for a Claude run's socket `home_too_long`, each exit 13, B3, B6. The README gives the limit: at most 55 bytes on
Linux, 51 on macOS.)*

#### 4.8.3 Uninstall (README)

Delete the app; delete `~/.deep-reasoning` (and `/var/tmp/deep-reasoning-<uid>` if it was used). uv's cache and
managed Pythons are shared with any other uv use and are left alone. *(v3: the README adds a folder chosen with
`dr-app home`, and Electron's own folders, `~/Library/Application Support/Deep Reasoning` and `~/.config/Deep
Reasoning`, read, not run, as-built §7; B18.)*

### 4.9 The App-backend ingress

*(v2: shortened. C3 built the default v1 asked for (#5, B2), so D5 sets nothing, and v1's fallback in setup, its
signatures, its test and its size are gone. What remains D5's is the proof in Electron's own Chromium.)* The
Library panel is D3's App page; the data it shows comes from D2's backend through the agent-server's bridge.

**What the bridge requires** (`canvas_extensions/bridge.py`, `canvas_extensions_bridge_router.py`; unchanged
since v1's pin):
- Every `/app-backends/<app>/…` route answers 503 "Canvas App backend ingress is not configured" until
  `app_backend_public_url` (`OH_APP_BACKEND_PUBLIC_URL`, `config.py:350`) names an http(s) origin (`:231–244`).
  *(v2: every launcher now sets it, `scripts/dev-safe.mjs:883–884`: the environment's value, else
  `http://127.0.0.1:<agent-server port>`; `/server_info` reports it as `app_backend_ingress_url`,
  `server_details_router.py:150`, which C2's frames read.)*
- Every request must arrive on that origin, judged by its own `Host` (`:296–301`). The session bootstrap
  (`POST /app-backends/<app>/session`, with the session key) must carry a loopback or allowed `Origin` that is
  not the ingress's own (`:304–314`), and is answered 409 otherwise.
- The session is an HttpOnly cookie, `Secure`, `SameSite=None`, `Partitioned`, scoped to `/app-backends/<app>`,
  for five minutes (`:33, 392–413`); on plain http it is issued only to a loopback host (`:376–389`).

**The origin: `http://127.0.0.1:<agent-server port>`** (18000 in the desktop app), with Canvas in the window at
`http://localhost:8000` (`electron/main.mjs:399`). The launcher binds the agent-server to 127.0.0.1
(`dev-with-automation.mjs:1126–1132`), so the frame reaches it directly with `Host: 127.0.0.1:18000`. It is another
origin than Canvas's (no 409), and another site: the frame is a cross-site context, so its cookie must be
`SameSite=None; Secure; Partitioned`, which is what the bridge issues; the partition key is Canvas's site, so the
cookie the Canvas page's own `fetch` stored is the one the frame sends. Loopback hosts are secure contexts, so
`Secure` holds over http. The agent-server's CORS admits loopback origins with credentials (`middleware.py:34–60`).
The flow, which C2's host code and D3's frame own:

```text
Canvas page (http://localhost:8000)
  fetch("http://127.0.0.1:18000/app-backends/dr-library/session",
        {method: "POST", credentials: "include", headers: {"X-Session-API-Key": <key>}})
     → {ingress_url: "http://127.0.0.1:18000/app-backends/dr-library/", expires_at}  + the partitioned cookie
  <iframe src=ingress_url + "ui/?…">  → every request carries the cookie → the bridge → dr-library serve
  renew before expires_at
```

**What it exposes.** Nothing new listens: the agent-server already serves 127.0.0.1:18000. An App request needs
that App's session cookie, which only a holder of the session key can mint; Canvas's `localhost` cookies are never
sent to the ingress, because it is another site.

**The proof, in the skeleton** (§7.5 step 5). *(v2: v1's probe App is gone; D3's own frame is the probe.)* With
the Library App installed, approved and started by setup, in the app's window over CDP: the session `fetch`; an
iframe at `ingress_url + "ui/?tab=namespaces&cap=5"`, D3's frame UI standalone (without `parent` it shows its own
tab row and posts nothing, D3 as-built §3.3); the frame shows D3's notice, whose text is `texts.safety("5")`; after
`dr-notice-ack`, the Namespaces tab lists the Library's namespaces (`dr-node-<namespace>`), which only D2's API,
reached through the bridge past D2's `Host` guard, can give; the cookie is listed with a partition key
(`Network.getCookies`); and the frame's next request is answered 401 after `DELETE …/session`. The final part
repeats it through C2's header button and D3's page (§7.5). *(v3: it holds in Electron's Chromium, E12's
`test_d3s_frame_works_through_the_bridge_in_electrons_chromium`: the cookie is `Secure; SameSite=None`, partitioned
under `http://localhost`, and the frame's next request is 401 once the session is deleted; the header panel keeps
working past its first five-minute session. Read with `Storage.getCookies`, B7.)*

---

## 5 · Signatures

Valid Python, one field per line, ruff-formatted. Bodies are `...`; docstrings say what tests pin.

*(v3: every block below is the code's at `3e9cee9`: the same names, parameters, defaults and docstrings, bodies
elided. A line marked `# v3:` differs from v2's block, with the B-number of §3.1 that changed it. Private helpers
(`_`-prefixed) are left out, as in v2.)*

### 5.1 `dr_app.layout`

```python
# v3: the exit codes, one table, and SetupError live here (B27); 14 is new (B21).
EXIT_USAGE: Final = 2  # as argparse's; after-ready without the launcher's variables
EXIT_CHECK: Final = 10  # a check before the install: nothing was installed
EXIT_INSTALL: Final = 11  # a step of the install: runtime/current is unchanged
EXIT_AGENT_SERVER: Final = 12  # the agent-server refused what setup depends on
EXIT_HOME: Final = 13  # the data home is unusable, or nothing is installed to export
EXIT_STATE: Final = 14  # setup.json is unusable: a newer app's, or damaged

ROOT_DIRNAME: Final = ".deep-reasoning"
CANVAS_DIRNAME: Final = "canvas"  # the agent-server's persistence root
# v3: no STATE_DIRNAME; AppLayout.state_dir is gone (B27).
NETWORK_HOME_TEMPLATE: Final = "/var/tmp/deep-reasoning-{uid}"
# D2's store.NETWORK_FILESYSTEMS, mirrored: this package imports nothing of
# deep-reasoning's, which uvx has not fetched when it runs.
NETWORK_FILESYSTEMS: Final = frozenset(
    {"nfs", "nfs4", "cifs", "smb3", "smbfs", "9p", "fuse.sshfs"}
)
MOUNTS: Final = Path("/proc/self/mounts")
# v3 (B3): sun_path's size less its terminating NUL: the longest path a Unix socket can bind.
SOCKET_PATH_MAX: Final = {"Linux": 107, "Darwin": 103}
# v3 (B3): the deepest socket setup makes room for under DR_HOME: a Claude-backed reasoner serves
# <run_dir>/repl.sock (deep_reasoner), D1 runs it in runs/<run id>, and each Claude
# sub-agent it spawns serves from children/<n> below it; room for one such level.
DEEPEST_SOCKET: Final = "runs/20261004-173501-a1b2c3/children/1000/repl.sock"
SETUP_STATE_VERSION: Final = 1


class SetupError(Exception):
    """A failure setup explains: its message is printed and dr-app exits with
    exit_code."""

    def __init__(
        self,
        exit_code: int,
        message: str,
    ) -> None: ...


@dataclass(frozen=True)
class AppLayout:
    root: Path

    @classmethod
    def default(cls) -> "AppLayout":
        """Path.home() / ROOT_DIRNAME."""

    @property
    def canvas(self) -> Path: ...

    @property
    def runtime_dir(self) -> Path: ...

    @property
    def current_runtime(self) -> Path: ...

    @property
    def bin_dir(self) -> Path: ...

    @property
    def canvas_app_dir(self) -> Path: ...

    @property
    def setup_file(self) -> Path: ...

    @property
    def lock_file(self) -> Path: ...


@dataclass(frozen=True)
class HomeChoice:
    path: Path
    reason: Literal["recorded", "default", "network-home"]
    filesystem: str | None  # Linux only


def filesystem_type(
    path: Path,
    *,
    mounts: Path = MOUNTS,
) -> str | None:
    """The type of the longest mount point prefixing path.resolve(); None off Linux."""


# v3 (B3)
def deepest_socket(home: Path) -> int:
    """The length in bytes of the deepest socket path setup makes room for under home."""


# v3 (B3)
def check_socket_room(
    home: Path,
    *,
    system: str,
) -> None:
    """Raises SetupError(13, texts.home_too_long(...)) when a Claude run's socket under
    home would be longer than the system lets a socket bind."""


def choose_home(
    layout: AppLayout,
    recorded: Path | None,
    *,
    system: str,
    uid: int,
    mounts: Path = MOUNTS,
    var_tmp: Path = Path(NETWORK_HOME_TEMPLATE).parent,  # v3: injectable for the tests
) -> HomeChoice:
    """§4.4.1: a recorded home that is still a local directory of ours; else the root,
    unless (Linux) it is on a network filesystem; else /var/tmp/deep-reasoning-<uid>.
    Raises SetupError(13, texts.home_unsafe(...)) for a /var/tmp directory that is not
    ours, and SetupError(13, texts.home_too_long(...)) for a home too long for a Claude
    run's socket."""


@dataclass
class RuntimeRecord:
    commit: str  # deep-reasoning's, whose uv.lock fixes everything else installed
    lock_sha256: str  # v3: that uv.lock's: what was synced, which no check reads (B22)
    path: str


@dataclass
class ProfileRecord:
    id: str
    activated_by_setup: bool


@dataclass
class CanvasAppRecord:
    digest: str
    version: str


@dataclass
class SetupState:
    v: int
    dr_home: str | None
    runtime: RuntimeRecord | None
    profile: ProfileRecord | None
    canvas_app: CanvasAppRecord | None

    @classmethod
    def load(
        cls,
        path: Path,
    ) -> "SetupState":
        """A fresh state when the file is absent. Raises SetupError(14, ...) with
        texts.state_from_a_newer_app for a version above 1, and texts.state_unusable,
        saying why, for a file no version of this app writes."""  # v3 (B21)

    def save(
        self,
        path: Path,
    ) -> None:
        """Atomic: a temporary file, then rename."""
```

### 5.2 `dr_app.runtime`

```python
PYTHON_VERSION: Final = "3.12"
# v3: no LOCK_RESOURCE, RuntimeSpec or SetupError here: the runtime is the commit's own
# tree (B22), and SetupError is dr_app.layout's (B27).
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
DEEP_REASONER: Final = "deep-reasoner"  # its package name in uv.lock
# The import check of §4.4.3: what dr-acp, dr-library and dr need at their start.
IMPORT_CHECK: Final = (
    "import deep_reasoning.acp.cli, deep_reasoning.library.cli, deep_reasoner"
)
# (decision P) How long the line pump may run on after its process has exited.
PUMP_DRAIN_S: Final = 1.0
READ_CHUNK: Final = 65536
Step = tuple[str, Sequence[str], Path | None]  # its name in install_failed, argv, cwd


def runtime_is_current(
    layout: AppLayout,
    record: RuntimeRecord | None,
    commit: str,  # v3: the commit, not a RuntimeSpec (B22)
) -> bool:
    """The record is the commit's (which fixes its uv.lock), runtime/current resolves to
    it, and its Python starts: one exec, offline."""


# v3: no injected run; the tests put stub git and uv on PATH.
def check_git() -> str:
    """git's version string. Raises SetupError(10, texts.NO_GIT)."""


def check_readable(url: str) -> None:
    """git ls-remote url HEAD. Raises SetupError(10, texts.no_access_dr(...)). Its output
    goes nowhere, so a credential helper that stays behind holds no pipe."""


# v3 (B22)
@dataclass(frozen=True)
class Pin:
    url: str  # https URL of the repository
    commit: str  # 40 hex


# v3 (B22)
def deep_reasoner_pin(source: Path) -> Pin:
    """deep_reasoner's repository and commit, as the tree's uv.lock pins them."""


def host_path(url: str) -> str:
    """https://github.com/a/b -> github.com/a/b, as the sentences name a repository."""


# v3 (B22)
@contextmanager
def fetched_source(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    log: Callable[[str], None],
) -> Iterator[Path]:
    """deep-reasoning's tree at commit, fetched alone, in runtime/ while it is needed;
    whatever an interrupted install left there is removed first. Raises
    SetupError(11, texts.install_failed(...)) naming the git step that failed."""


def install_runtime(
    layout: AppLayout,
    source: Path,  # v3: the fetched tree (B22)
    commit: str,
    *,
    uv: str,
    log: Callable[[str], None],
) -> RuntimeRecord:
    """§4.4.3: a venv on uv's own Python, every workspace package of source synced into
    it from its uv.lock (no dev group, nothing editable), the import check, then the
    rename and the link. Raises SetupError(11, texts.install_failed(...)) on any
    non-zero step, leaving runtime/current as it was."""


def run_logged(
    argv: Sequence[str],
    *,
    env: Mapping[str, str],
    log: Callable[[str], None],
    cwd: Path | None = None,
) -> int:
    """argv's exit code. stdout and stderr share one pipe; each line goes to log as it
    arrives. Returns at the process's exit, after at most PUMP_DRAIN_S more of reading: a
    grandchild that keeps the pipe never holds it. Never starts a new session."""


def git_environment(
    base: Mapping[str, str],
) -> dict[str, str]:
    """base plus GIT_TERMINAL_PROMPT=0 and, unless set, GIT_SSH_COMMAND='ssh -o
    BatchMode=yes'."""
```

### 5.3 `dr_app.agent_server`

```python
class AgentServerError(Exception):
    def __init__(
        self,
        method: str,
        path: str,
        status: int,
        detail: Any,
    ) -> None: ...


class AgentServer:
    """The agent-server's REST API with the session key; never through an HTTP proxy."""

    def __init__(
        self,
        url: str,
        session_key: str,
        *,
        timeout_s: float = 60.0,
    ) -> None: ...

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
    ) -> Any:
        """JSON in and out; 404 returns None; any other non-2xx raises AgentServerError,
        as does an agent-server that cannot be reached (status 0)."""  # v3: status 0

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str],
    ) -> "AgentServer":
        """AGENT_SERVER_URL and SESSION_API_KEY (C3 §4.2). Raises SetupError(2, …) if
        either is missing."""  # v3: the sentence is texts.NO_AGENT_SERVER (B6)
```

*(v3: the E12 and cross-repo harnesses use this class too, B29.)*

### 5.4 `dr_app.profile`

```python
PROFILE_NAME: Final = "deep_reasoner"
HOME_FLAG: Final = "--home"
SPEND_CAP_FLAG: Final = "--spend-cap-usd"
DEFAULT_SPEND_CAP_USD: Final = "5"
OWNED_FIELDS: Final = ("agent_kind", "acp_server", "acp_command", "acp_subagents")
PROFILES: Final = "/api/agent-profiles"  # v3


def desired_profile(
    existing: Mapping[str, Any] | None,
    *,
    dr_acp: Path,
    home: Path,
) -> dict[str, Any]:
    """§4.5.1's table: the owned fields (acp_subagents always true) and the --home pair
    set, everything else kept from existing."""


def needs_write(
    existing: Mapping[str, Any] | None,
    want: Mapping[str, Any],
) -> bool:
    """No profile yet, or an owned field or the arguments differ."""  # v3: and acp_args


def ensure_profile(
    server: AgentServer,
    state: SetupState,
    *,
    dr_acp: Path,
    home: Path,
    log: Callable[[str], None],
) -> ProfileRecord:
    """§4.5.1, steps 1–5. Any refusal raises SetupError(12,
    texts.agent_server_failed(...))."""  # v3: the id from the profile's own GET (B25)
```

### 5.5 `dr_app.canvas_app` (*v2:* skeleton)

```python
# D3's deep_reasoning.canvas_app.APP_NAME, mirrored: this package imports nothing of
# deep-reasoning's.
APP_NAME: Final = "dr-library"
# D3's built files, in the runtime (§8.3)
APP_PACKAGE: Final = "deep_reasoning.canvas_app"
# The only files staged; ui/ is served by dr-library serve itself (D3 §8.4 item 1).
STAGED_FILES: Final = ("canvas-extension.json", "dist/index.js", "panel.svg")
MANIFEST: Final = STAGED_FILES[0]  # v3
ARTIFACT_PATH: Final = "backend/dr-library.tar.gz"
ARTIFACT_MEMBER: Final = "bin/dr-library"  # v3
# The agent-server passes a backend only these (backend.py:38–40).
INHERITED_ENVIRONMENT: Final = ("LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ")
PLATFORMS: Final = {"Linux": "linux", "Darwin": "darwin"}  # v3
INSTALLED: Final = f"/api/canvas-extensions/installed/{APP_NAME}"  # v3


@dataclass(frozen=True)
class StagedApp:
    path: Path
    digest: str
    version: str
    manifest: Mapping[str, Any]


def backend_artifact(dr_library: Path) -> bytes:
    """The deterministic .tar.gz of §4.6 step 2: equal inputs give equal bytes. One
    member, bin/dr-library, a /bin/sh script that execs dr_library."""


def backend_block(
    *,
    system: str,
    sha256: str,
    home: Path,
) -> dict[str, Any]:
    """The manifest's backend: both architectures name the same script, which runs on
    either; the home is a literal, since the backend gets no DR_HOME or HOME."""


# v3
def app_files(layout: AppLayout) -> Path:
    """Where D3's built files are in the runtime."""


def stage_canvas_app(
    layout: AppLayout,
    *,
    home: Path,
    system: str,
) -> StagedApp:
    """§4.6 steps 1–4: the three files, the artifact and the manifest with its backend
    under canvas-app/<digest>/, reused when it is there."""


def ensure_canvas_app(
    server: AgentServer,
    staged: StagedApp,
    state: SetupState,
    *,
    log: Callable[[str], None],
) -> CanvasAppRecord | None:
    """§4.6 step 5. Never raises for the agent-server's refusals: they become
    texts.app_warning(...). The record is what is installed now."""
```

*(v2: `ensure_ingress_config`, `DESKTOP_AGENT_SERVER_PORT` and `AGENT_SERVER_CONFIG_RELATIVE` are gone with §4.9's
fallback; `ensure_canvas_app` no longer serves a probe App, so it uses `APP_NAME`.)*

### 5.6 `dr_app.cli`

```python
# v3: the exit codes are dr_app.layout's (B27).
PHASES: Final = ("before-start", "after-ready")
PHASE_ENV: Final = "OH_CANVAS_SETUP_PHASE"
LINKED: Final = ("dr-app", "dr")  # in bin/, to the runtime's own
SECRETS: Final = "/api/settings/secrets"
MODEL_KEY: Final = "OPENAI_API_KEY"
NOT_A_MODEL_KEY: Final = "OPENHANDS_AUTOMATION_API_KEY"


def say(line: str) -> None:
    """One line of the startup log."""


def duration(seconds: float) -> str:
    """1m 52s, or 4s."""


@contextmanager
def setup_lock(layout: AppLayout) -> Iterator[None]:
    """setup.lock held exclusively: a terminal run and a launch never interleave."""


def before_start(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    env: Mapping[str, str],
) -> None:
    """§4.4: the data home, then the runtime when it is not current, then bin/'s links."""


# v3 (B22, B23)
def install(
    layout: AppLayout,
    repo: str,
    commit: str,
    *,
    first: bool,
    env: Mapping[str, str],
) -> RuntimeRecord:
    """§4.4 steps 4 and 5: the checks, which leave nothing installed when one fails,
    then the runtime from the commit's own tree."""


def model_key_missing(server: AgentServer) -> bool:
    """No OPENAI_API_KEY, and no other secret named like a provider key."""


def after_ready(
    layout: AppLayout,
    *,
    env: Mapping[str, str],
) -> None:
    """§4.5: the agent profile, the model-key hint, the Library App."""


def main(argv: Sequence[str] | None = None) -> int:
    """dr-app setup [--phase PHASE] --repo URL --commit SHA | export DIR [--namespace
    NAME] | home [DIR]."""
```

### 5.7 `deep_reasoning.acp.proxy`

```python
# v3: no DEFAULT_SPEND_CAP_USD here; dr-acp's cli.py holds it (B28).
DEFAULT_RESERVED_OUTPUT_TOKENS: Final = 4096
MAX_BODY_BYTES: Final = 32 * 1024 * 1024
MIN_SECRET_LENGTH: Final = 16
OPENAI_DEFAULT_BASE_URL: Final = "https://api.openai.com/v1"
ANTHROPIC_DEFAULT_BASE_URL: Final = "https://api.anthropic.com"
ANTHROPIC_KEY_ENV: Final = "ANTHROPIC_API_KEY"
ANTHROPIC_BASE_URL_ENV: Final = "ANTHROPIC_BASE_URL"  # v3
OPENAI_BASE_URL_ENV: Final = "OPENAI_BASE_URL"  # v3
# build_client's fallback, config.py:256
OPENAI_FALLBACK_KEY_ENV: Final = "OPENAI_API_KEY"
# ClientConfig.api_key_env's default
DEEP_REASONER_DEFAULT_KEY_ENV: Final = "NOVITA_API_KEY"
LOOPBACK_HOSTS: Final = ("127.0.0.1", "::1", "localhost")
NO_PROXY_HOSTS: Final = "127.0.0.1,localhost,::1"  # v3
UPSTREAM_TIMEOUT: Final = httpx.Timeout(600.0, connect=10.0)  # v3
# Not forwarded either way: the connection's own, and what the proxy sets itself.
HOP_BY_HOP: Final = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)
# v3 (B5): the token's headers and accept-encoding are never forwarded, content-encoding
# never returned.
NOT_FORWARDED: Final = HOP_BY_HOP | {
    "host",
    "cookie",
    "content-length",
    "authorization",
    "x-api-key",
    "accept-encoding",
}
NOT_RETURNED: Final = HOP_BY_HOP | {"content-length", "content-encoding"}
REDACTED: Final = b"[redacted]"

Dialect = Literal["openai", "anthropic"]

# v3: plain dicts, not MappingProxyType (B28).
METERED_PATHS: Final[Mapping[Dialect, frozenset[str]]] = {
    "openai": frozenset({"chat/completions", "completions", "embeddings"}),
    "anthropic": frozenset({"v1/messages"}),
}
FREE_PATHS: Final[Mapping[Dialect, frozenset[str]]] = {
    "openai": frozenset(),
    "anthropic": frozenset({"v1/messages/count_tokens"}),
}


@dataclass(frozen=True)
class Route:
    id: str  # 16 hex, the URL's only identifier
    session: str
    run: str
    dialect: Dialect
    upstream: str  # base URL without a trailing slash
    key: str = field(repr=False)
    token_sha256: bytes = field(repr=False)


@dataclass(frozen=True)
class Reservation:
    session: str
    usd: float


# v3 (B28): the ledger's own account, mutable; no session or cap in it.
@dataclass
class Spend:
    """One root session's account."""

    spent_usd: float = 0.0
    reserved_usd: float = 0.0
    calls: int = 0
    refused: int = 0


class SpendLedger:
    """Per root session; persisted at <home>/spend/<session>.json; thread-safe."""

    cap_usd: float  # v3 (B28): the cap in force, set from __init__'s

    def __init__(
        self,
        home: Home,
        cap_usd: float,
    ) -> None: ...

    def reserve(
        self,
        session: str,
        usd: float,
    ) -> Reservation | None:
        """None (and refused += 1) when spent + reserved + usd > cap."""

    def settle(
        self,
        reservation: Reservation,
        usd: float,
    ) -> None:
        """The reservation replaced by the call's cost."""

    def spend(
        self,
        session: str,
    ) -> Spend:
        """A copy of the session's account."""  # v3 (B28)


class KeyProxy:
    """The HTTP side: 127.0.0.1 only, its own thread, started on first use."""

    def __init__(
        self,
        *,
        ledger: SpendLedger,
        prices: PriceTable,
        home: Home,
    ) -> None: ...

    def ensure_started(self) -> None:
        """Bind 127.0.0.1:0 (so the port is known), then serve on a thread of its own;
        returns once the server accepts connections."""

    def stop(
        self,
        timeout_s: float = 0.5,
    ) -> None: ...

    @property
    def base_url(self) -> str:
        """http://127.0.0.1:<port>; only after ensure_started()."""

    def add_route(
        self,
        *,
        session: str,
        run: str,
        dialect: Dialect,
        upstream: str,
        key: str,
        token: str,
    ) -> Route: ...

    def drop_run(
        self,
        run: str,
    ) -> None:
        """The run's routes, and so its tokens, stop working; calls in flight finish."""

    def app(self) -> Starlette:
        """The ASGI app of §4.7.3, which ensure_started serves."""


def is_loopback(url: str) -> bool: ...


def loopback_proxy_env(
    env: Mapping[str, str],
    *,
    system: str,
    system_proxies: Callable[[], Mapping[str, str]] = urllib.request.getproxies,
) -> dict[str, str]:
    """§4.7.2 step 5: NO_PROXY with the loopback hosts appended; on macOS with no proxy in
    env, the system's http and https proxies as HTTP_PROXY and HTTPS_PROXY."""


class ProxyRoute:
    """D1's ModelRoute over a KeyProxy (§4.7.2)."""

    def __init__(
        self,
        proxy: KeyProxy,
        env: Mapping[str, str],
    ) -> None: ...

    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = NO_TOOL_UPSTREAMS,  # v3: route.py's
    ) -> RouteGrant: ...

    def release(
        self,
        run: str,
    ) -> None: ...
```

`deep_reasoning.acp.cli` gains two constants and `Options` two fields after D1's five (*v3:* as built, B28):

```python
DEFAULT_SPEND_CAP_USD = 5.0  # per conversation, through the key proxy
PROXY_STOP_S = 0.5  # inside D1's shutdown budget


@dataclass(frozen=True)
class Options:
    ...  # D1's config, home, flat, heartbeat_s, log_level
    key_proxy: bool  # off with --no-key-proxy: the worker gets the keys themselves
    spend_cap_usd: float  # --spend-cap-usd USD, default 5
```

### 5.8 `desktop/build.py`

```python
REPO: Final = Path(__file__).resolve().parents[1]
# What every user's setup fetches (§4.2.3).
DEEP_REASONING: Final = "https://github.com/michaeltheologitis/deep-reasoning"
GITHUB: Final = "https://github.com/"
GITHUB_API: Final = "https://api.github.com"  # v3 (B24)
GITHUB_RAW: Final = "https://raw.githubusercontent.com"  # v3 (B24)
PINS: Final = REPO / "desktop" / "pins.toml"
BOOTSTRAP: Final = REPO / "desktop" / "bootstrap.sh"
WRAPPER_CONFIG: Final = REPO / "desktop" / "electron-builder.dr.mjs"
COMMIT: Final = re.compile(r"[0-9a-f]{40}")
# The branch every pinned fork commit must be on (§4.2.2 check 8).
FORK_BRANCH: Final = "deep-reasoning"
STATE_DIR: Final = "~/.deep-reasoning/canvas/agent-canvas"
SETUP_PHASES: Final = ["before-start", "after-ready"]
BOOTSTRAP_NAME: Final = "dr-app-bootstrap"
TYPESCRIPT_CLIENT: Final = "@openhands/typescript-client"
ACP_PYTHON: Final = "agent-client-protocol"
# v3 (B14): two targets, each built on its own machine; Macs are Apple silicon only.
ARTIFACT_KINDS: Final = {
    "linux": ("AppImage", "deb"),
    "mac-arm64": ("dmg",),
}
BUILD_MACHINES: Final = {
    "linux": ("Linux", "x86_64"),
    "mac-arm64": ("Darwin", "arm64"),
}
MAC_ARCH: Final = "arm64"
MAC_MINIMUM: Final = "14.0"  # v3 (B19)
# What the .app carries that must run on Apple silicon: Electron, uv and Node.
MAC_BINARIES: Final = (
    "MacOS/{product}",
    "Resources/bin/uv",
    "Resources/node/bin/node",
)
FORBIDDEN_IN_PAYLOAD: Final = "deep_reasoner"


@dataclass(frozen=True)
class ForkPin:
    repo: str
    commit: str
    tag: str


@dataclass(frozen=True)
class AppPin:
    product_name: str
    app_id: str
    executable_name: str
    version: str
    maintainer: str
    uv_version: str


@dataclass(frozen=True)
class Pins:
    canvas_fork: ForkPin
    sdk_fork: ForkPin
    app: AppPin


Target = Literal["linux", "mac-arm64"]  # v3 (B14): not linux, mac, mac-universal


def load_pins(path: Path) -> Pins:
    """Raises ValueError naming the key for a commit that is not 40 hex."""


def check_pins(
    pins: Pins,
    *,
    canvas: Path,
    repo: Path,
    ls_remote: Callable[[str, Sequence[str]], Mapping[str, str]],
    read_sdk_file: Callable[[str], str],
    is_on_branch: Callable[[str, str, str], bool],
) -> list[str]:
    """§4.2.2's checks; the problems as sentences, empty when the pins belong together.
    The readers stand for the forks' repositories: ls_remote(url, refs) gives each ref's
    commit, read_sdk_file(path) a file at the SDK fork's commit, and
    is_on_branch(url, branch, commit) answers check 8."""


def setup_command(
    repo_url: str,
    commit: str,
    bootstrap: str,
) -> list[str]:
    """The setup command C3's launcher runs: sh -c <bootstrap> with the dr-app package,
    deep-reasoning's repository and the commit as $1, $2 and $3."""


def patch_defaults(
    defaults: Mapping[str, Any],
    *,
    state_dir: str,
    command: list[str],
) -> dict[str, Any]:
    """§4.2.3's four keys; every other key unchanged."""


# v3 (B24): the readers of the forks' public repositories, git and GitHub's REST API.
def git_ls_remote(
    repo_url: str,
    refs: Sequence[str],
) -> dict[str, str]: ...


def read_file_at(
    repo_url: str,
    commit: str,
    path: str,
) -> str: ...


def is_on_branch(
    repo_url: str,
    branch: str,
    commit: str,
) -> bool:
    """GitHub finds the branch identical to commit, or ahead of it; it knows no such
    commit on none. GITHUB_TOKEN, when set, lifts the API's 60 requests an hour."""


def checkout_canvas(
    pins: Pins,
    work: Path,
) -> Path:
    """The Canvas fork at its pinned commit under work/canvas, nothing else changed."""


def check_checkouts(
    pins: Pins,
    *,
    repo: Path,
    work: Path,
) -> tuple[Path, list[str]]:
    """The Canvas checkout under work, and check_pins against the forks' repositories."""


def build(
    target: Target,
    *,
    pins: Pins,
    repo: Path,
    work: Path,
) -> list[Path]:
    """Check out the Canvas fork at its commit under work/, check, patch, build, verify;
    the artifacts, copied to <repo>/dist/."""


def payload_paths(
    artifact: Path,
    canvas: Path,
) -> list[str]:
    """Every path the package carries: a .deb's listing; for the rest, the unpacked tree
    electron-builder made it from."""


def macho_archs(path: Path) -> str:
    """The architectures of a Mach-O file, as lipo names them ("arm64", "x86_64 arm64")."""


# v3 (B14, B19)
def verify(
    target: Target,
    pins: Pins,
    canvas: Path,
    *,
    archs_of: Callable[[Path], str] = macho_archs,
) -> list[Path]:
    """Exactly the expected artifacts, named deep-reasoning-<version>-<arch>.<ext> (the
    .dmg's arch arm64), no deep_reasoner inside any, and for the Mac the .app's Electron,
    uv and Node arm64 only, and its Info.plist's minimum macOS MAC_MINIMUM."""


def main(argv: Sequence[str] | None = None) -> int:
    """uv run desktop/build.py {linux|mac-arm64|check} [--work DIR]."""
```

*(v3: left out above, as private in all but name: the build's sentences, one function per refusal, which §6 lists, and
the helpers `git`, `run` and `locked_version`.)*

---

## 6 · Texts (verbatim; tests assert these)

`dr-app` (`dr_app.texts`). *(v2, decision O)* A name in capitals is a constant, a sentence without fields; a
name in lower case is a function that returns the sentence with its fields filled, its parameters the fields, in
order, as `str` (`safety(cap: str) -> str`), like D1's and D2's texts modules. `SUBAGENTS_UNSUPPORTED` is gone, and
the two profile sentences lose their `{on_off}`, with the flat fallback (§4.5.1).

| Name | Text |
|---|---|
| `NO_GIT` | `✗ deep_reasoner is fetched with git, which was not found. On macOS run xcode-select --install; on Linux install git.` |
| `NO_UV` | `✗ uv was not found on PATH. The app bundles it: reinstall the app. In a terminal, install uv from https://docs.astral.sh/uv/.` |
| `no_access_dr(host_path)` | `✗ Could not read {host_path} with your git credentials. It is private: ask Dean for read access, then sign git in for https (gh auth login, or an SSH key and git config --global url."git@github.com:".insteadOf "https://github.com/") and restart. Nothing was installed.` |
| `checks_ok(version, host_path)` | `git {version} ✓ · {host_path} readable ✓` |
| `safety(cap)` | `deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at ${cap} per conversation.` |
| `installing(commit7, dr_commit7)` | `installing deep-reasoning {commit7} with deep_reasoner {dr_commit7} … (first launch, or after an update: a few minutes)` |
| `installed(duration)` | `installed in {duration}` |
| `install_failed(commit7, step, code)` | `✗ Installing deep-reasoning {commit7} failed ({step} exited {code}); its output is above. After an update this needs the network once: connect and restart.` |
| `home_local(home)` | `your data: {home}` |
| `home_network(fstype, home)` | `Your home directory is on a network filesystem ({fstype}), where the Library's database is unsafe, so your data is kept on this computer at {home}. The system may delete files there that go unused for 30 days: export your Library now and then (dr-app export DIR), or choose another folder with dr-app home DIR.` |
| `home_unsafe(path, owner, mode)` | `✗ {path} exists but is not a private folder of yours (owner {owner}, mode {mode}). Remove it, or choose another folder with dr-app home DIR.` |
| `home_set(home, old)` | `Your data will be kept in {home} from the next launch. Nothing was moved: copy library.sqlite, runs/, sessions/ and spend/ from {old} yourself, or export the Library and import it there.` |
| `PROFILE_CREATED` | `agent profile deep_reasoner created and made the default` |
| `PROFILE_UPDATED` | `agent profile deep_reasoner updated` |
| `NO_MODEL_KEY` | `No model key is saved yet: add OPENAI_API_KEY under Settings → Secrets before your first question.` |
| `agent_server_failed(method, path, status, detail)` | `✗ The agent-server refused {method} {path} ({status}): {detail}` |
| `app_ready(version, installed_or_current)` | `App dr-library {version} {installed_or_current} · backend ready` |
| `APP_DISABLED` | `App dr-library is disabled, so Show decompositions is hidden. Enable it under Apps to use it.` |
| `APP_UNSUPPORTED` | `⚠ This agent-server cannot run the Library panel's backend on this platform; conversations still work.` |
| `app_warning(detail)` | `⚠ The Library panel's backend did not start ({detail}); conversations still work. Its log is under Apps → dr-library.` |
| `NOTHING_INSTALLED` | `✗ Nothing is installed yet: launch the app once, then run this again.` |
| *(v3, B6)* `NO_AGENT_SERVER` | `✗ The after-ready phase needs AGENT_SERVER_URL and SESSION_API_KEY, which the app's launcher sets.` |
| *(v3, B3)* `home_too_long(home, length, limit)` | `✗ {home} is too long a path for your data: deep_reasoner's Claude runs serve sockets under it up to {length} bytes long, and this system allows {limit}. Choose a shorter folder with dr-app home DIR.` |
| *(v3, B6)* `home_refused(path, reason)` | `✗ {path} {reason}: choose an absolute path to a folder on this computer with dr-app home DIR.` (`reason`: `is not an absolute path`, or `is on a network filesystem ({fstype})`) |
| *(v3, B21)* `state_from_a_newer_app(path, version)` | `✗ {path} was written by a newer Deep Reasoning (its version {version}; this one reads 1). Install the newer app again. To set this one up from the start instead, delete {path}: your data stays, but a folder chosen with dr-app home is forgotten.` |
| *(v3, B21)* `state_unusable(path, reason)` | `✗ {path} cannot be used: {reason}. Delete it and launch the app again: setup then installs as on a first launch, which needs the network. Your data stays, but a folder chosen with dr-app home must be chosen again.` (`reason`, one of six: `it cannot be read ({strerror})`, `it is not JSON`, `it is not a JSON object`, `its version is {v as JSON}`, `it has no version`, `it holds a record this app does not write`) |

*(v3: every sentence in both tables is the code's, verbatim; the as-built compared each, its §5.4. `install_failed`'s
`step` is now one of `git init`, `git fetch`, `git checkout`, `uv venv`, `uv sync` or `the import check`, B22.)*

The bootstrap's two lines are §4.3.1's. The key proxy (`deep_reasoning.acp.texts`, D1's module):

| Name | HTTP | Text |
|---|---|---|
| `cap_reached(spent, cap)` | 402 | `The key proxy refused this model call: this conversation has spent ${spent:.2f} of its ${cap:.2f} cap. Start a new conversation, or raise the cap (--spend-cap-usd in the deep_reasoner agent profile's arguments).` |
| `unpriced(model, home)` | 400 | `The key proxy refused a call to '{model}': its price is unknown, so the spend cap cannot bound it. Add it to {home}/prices.yaml (input and output USD per million tokens), then send your message again.` |
| `not_a_model_call(paths, method, rest)` | 403 | `The key proxy forwards only model calls ({paths}); {method} /{rest} was refused.` |
| `BAD_TOKEN` | 401 | `The key proxy does not know this token.` |
| `upstream_unreachable(host, error)` | 502 | `The key proxy could not reach {host}: {error}.` |
| *(v3, B5)* `bad_body(rest, mib)` | 400 | `The key proxy forwards to /{rest} only a JSON object of at most {mib} MiB; this body was refused.` |

Error bodies take the dialect's shape: `{"error": {"message", "type", "code"}}` for `openai`,
`{"type": "error", "error": {"type", "message"}}` for `anthropic`, with `type` and `code` the name in lower case
(`cap_reached`, `bad_token`, …). `cap_reached` and `unpriced` take floats and a path where the table shows them
formatted (`{spent:.2f}`); the rest take `str`.

The build: `✗ Canvas fork {canvas_tag} runs the agent-server at {wired7} (its wiring commit), but desktop/pins.toml
pins the SDK fork at {sdk_tag} ({sdk7}). Bump both, or neither.`, and one sentence per other check of §4.2.2,
each naming the file and the two values that disagree.

*(v3: as built, one function each in `build.py`; `{x7}` is the first seven characters of a commit.)*

| Name | Text |
|---|---|
| `tag_moved(fork, tag, found, commit)` (check 1) | `✗ The {fork} tag {tag} resolves to {found7, or nothing}, but desktop/pins.toml pins {commit7}. Move the tag, or the pin.` |
| `wired_to_another_repo(canvas_tag, wired_repo, sdk_repo)` (check 2) | `✗ Canvas fork {canvas_tag}'s config/defaults.json runs the agent-server from {wired_repo}, but desktop/pins.toml pins the SDK fork {sdk_repo}.` |
| `wired_elsewhere(canvas_tag, wired, sdk_tag, sdk)` (check 2) | v2's sentence, above |
| `client_from_elsewhere(canvas_tag, spec, sdk_tag)` (check 3) | `✗ Canvas fork {canvas_tag}'s package.json takes @openhands/typescript-client from {spec}, not from the SDK fork's release {sdk_tag}.` |
| `acp_differs(sdk_tag, theirs, ours)` (check 4) | `✗ The SDK fork's uv.lock at {sdk_tag} locks agent-client-protocol {theirs}, but deep-reasoning's uv.lock locks {ours}: both ends must run one ACP Python.` |
| `fork_sets_ours(canvas_tag, key, value)` (check 5) | `✗ Canvas fork {canvas_tag}'s config/defaults.json sets {key} to {value as JSON}; the fork must leave it null, for this build to write.` |
| `checkout_dirty(changed)` (check 6) | `✗ This deep-reasoning checkout has {changed} uncommitted change(s): every user's setup fetches the commit, so build from a clean checkout.` |
| `head_unpushed(head)` (check 6) | `✗ deep-reasoning's HEAD ({head7}) is on no branch of origin: every user's setup fetches it, so push it first.` |
| `off_branch(fork, commit)` (check 8) | `✗ The {fork} commit {commit7} is not on its deep-reasoning branch: pin a commit its stacks merged there.` |
| `wrong_machine(target, system, machine)` (B14) | `✗ desktop/build.py {target} builds for {its system} on {its machine}, the machine it runs on, and this one is {system} on {machine}.` |
| `not_arm64(binary, archs)` (B14) | `✗ {binary} is {archs}, not arm64 only: Macs are Apple silicon only.` |
| `opens_too_early(declared)` (B19) | `✗ The app's Info.plist declares LSMinimumSystemVersion {declared}, not 14.0: desktop/electron-builder.dr.mjs's mac block sets it.` |

`build.py check` prints `the pins belong together ✓` when every check passes, and the problems, one per line, when
not.

What the startup log shows at a first launch (the splash prefixes each line with its service, C3 §3.3):

```text
[defaults]           From config/defaults.json: OH_AGENT_SERVER_GIT_REF, OH_AGENT_SERVER_GIT_REPO, OH_CANVAS_SAFE_STATE_DIR, OH_SECRET_KEY_PATH, OH_SESSION_API_KEY_PATH
[setup before-start] Running sh -c … dr-app-bootstrap …
[setup before-start] your data: /Users/u/.deep-reasoning
[setup before-start] git 2.39.5 ✓ · github.com/DeanLight/deep_reasoner_beta readable ✓
[setup before-start] deep_reasoner runs as you. It can read and change any file you can, … stops at $5 per conversation.
[setup before-start] installing deep-reasoning a1b2c3d with deep_reasoner d7334ae … (first launch, or after an update: a few minutes)
[setup before-start] … uv's own lines …
[setup before-start] installed in 1m 52s
[setup before-start] Done in 1m 58s
[agent-server]       Using git (michaeltheologitis/software-agent-sdk@34c540ce0598b20ddf913d51968dd903c1c13b2e)
[setup after-ready]  Running sh -c … dr-app-bootstrap …
[setup after-ready]  agent profile deep_reasoner created and made the default
[setup after-ready]  No model key is saved yet: add OPENAI_API_KEY under Settings → Secrets before your first question.
[setup after-ready]  App dr-library 0.1.0 installed · backend ready
[setup after-ready]  Done in 4s
```

*(v2)* The `[defaults]` names are sorted, and each phase is framed by the launcher's own `Running …` and `Done in …`
lines (C3 v3 §3.3, B5); the App's version is deep-reasoning's package version, `0.1.0` today (D3 B5).

*(v3: as built, the lines are these, in this order. `git fetch -q` and `git checkout -q` print nothing on success, so
the fetch of the commit's tree before `checks_ok` is silent. The macOS runner's launch log at `3e9cee9` reads
`installed in 12s` and `Done in 17s` for before-start, and `Done in 2s` for after-ready, as-built §5.2.)*

---

## 7 · Testing and CI

Plain pytest, each test named for the property it pins; the outside world faked at its boundary (a stub `uv`,
`uvx` and `git` on `PATH` as small scripts that record their argv; an in-test HTTP server answering like the
agent-server; D1's `FakeOpenAI` as the provider). Layer 1 (every push) unless marked.

### 7.1 E10: keys and the spend cap (two automated tests, and the proxy's units)

`tests/acp/test_e10_keys.py`, through `dr-acp` over stdio with D1's harness (`ShimConnection`, `FakeOpenAI`):

- **`test_provider_keys_and_agent_server_secrets_never_reach_the_worker_a_cell_the_transcript_or_the_run_log`**
  (E10 #1). `dr-acp`'s environment holds `OPENAI_API_KEY=sk-e10-<random>`, an alias `MY_KEY_COPY` with the same
  value, `ANTHROPIC_API_KEY`, and random `OH_SECRET_KEY`, `OH_SESSION_API_KEYS_0`, `SESSION_API_KEY`,
  `OPENHANDS_AUTOMATION_API_KEY`. A config of our own points the client at `FakeOpenAI` (loopback) with
  `api_key_env: OPENAI_API_KEY`, a tool block `rag`-shaped with its own `client` naming the same key, and model
  `e10-model` priced in `<home>/prices.yaml`. The fake's responder writes a cell that prints `dict(os.environ)`,
  `open("/proc/self/environ", "rb").read()` and the environment of a child (`subprocess.run(["env"])`), then
  answers. Asserts: none of the secret values (nor their base64) appears in the worker's
  `/proc/<pid>/environ` (pid from the run log's `worker.ready`), in the cell's output, in any update the client
  received, in `events.jsonl`, `worker.log` or any other file under the run's directory, or in `dr-acp`'s stderr;
  the fake received `Authorization: Bearer sk-e10-…` on every call (the proxy swapped it in), for the main client
  and the tool's; the worker's `OPENAI_API_KEY` is a token. Linux only (`/proc`); skipped elsewhere with a reason.
  (D1's `FakeCall`, in `deep_reasoning.acp.testing.fake_model`, gains the call's `Authorization` header for this;
  a test helper, not a seam.)
- **`test_a_call_past_the_spend_cap_is_refused_and_never_forwarded`** (E10 #2). `--spend-cap-usd 0.01`; the config
  sets `max_iter: 50` and `llm_kwargs.max_tokens`, so the reservation is near the cost and the run outlasts the
  cap; the fake reports usage worth $0.004 per call and its responder never answers, so the agent keeps calling. Asserts: the
  run ends `failed` with `cap_reached` in its detail; the fake saw exactly the calls the ledger counted, and none
  after the first refusal; `spend/<session>.json` records `spent_usd ≤ 0.01 + one call's overshoot` and
  `refused ≥ 1`; a second prompt in the same conversation is refused at once, and so is one after `dr-acp` is
  killed and the session reloaded.

`tests/acp/test_key_proxy.py`, the proxy in process (`httpx.ASGITransport` in front, a fake upstream behind):

`test_the_token_is_swapped_for_the_key_and_the_call_forwarded` ·
`test_a_wrong_or_missing_token_is_refused_and_nothing_is_forwarded` ·
`test_only_model_endpoints_are_forwarded` (parametrized: `files`, `fine_tuning/jobs`, `batches`, `images`, a GET
on a metered path) · `test_a_route_forwards_only_to_its_configured_upstream` ·
`test_an_unpriced_model_is_refused_unless_the_upstream_is_loopback` ·
`test_concurrent_calls_overshoot_the_cap_by_at_most_their_reservations` (20 at once) ·
`test_a_streamed_openai_call_is_metered_from_its_last_chunk` (and `include_usage` is injected) ·
`test_a_streamed_anthropic_call_is_metered_from_message_start_and_delta` ·
`test_upstream_error_bodies_never_echo_the_key` · `test_a_released_runs_tokens_stop_working` ·
`test_the_ledger_continues_after_a_restart` · `test_a_client_without_a_held_key_is_left_as_configured` ·
`test_the_key_is_removed_from_the_worker_env_by_value_under_any_name` ·
`test_loopback_calls_bypass_macos_system_proxies_and_others_keep_them` (`system_proxies` faked) ·
`test_the_proxy_never_logs_a_key_or_a_token` · `test_no_key_proxy_keeps_d1s_direct_route`.

E10 runs again in the final part with D4's MCP servers bound in the worker (the same assertions; D4's
`echo_server.py` and its grant, §8.7), and inside the real app in E12.

*(v3: built, all of it, at `3e9cee9`. E10 #2 as run: all three prompts (the first, a second, one after `dr-acp`
restarted and reloaded the session) end `failed` with the proxy's sentence, the fake saw exactly the calls the ledger
counted, `spent_usd` ≤ $0.014 and `refused` ≥ 3. E10 with D4's server is
`test_an_mcp_server_gets_a_provider_key_only_when_its_settings_name_it_and_the_worker_never_does[unnamed, named]`, B9.
`test_key_proxy.py` has the sixteen above and four more: `test_an_anthropic_route_swaps_the_x_api_key`,
`test_provider_errors_release_their_reservations` and
`test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused` (B4), and
`test_a_tool_with_its_own_client_gets_its_own_overrides`. D1's files gain
`test_catalog.py::test_materialize_hands_the_worker_each_tools_own_client`,
`test_runner.py::test_the_run_config_takes_the_namespace_and_every_clients_overrides` and
`::test_a_start_without_tool_overrides_leaves_every_tool_as_configured`, and `test_texts.py`'s
`test_the_key_proxys_sentences_are_d5s_verbatim`. No test pins `bad_body` or the uncompressed path, B5.)*

### 7.2 `dr-app`

| File | Pins |
|---|---|
| `tests/app/test_layout.py` | `test_the_default_home_is_the_root_when_it_is_local`; `test_a_network_home_moves_the_data_to_var_tmp` (a fake `/proc/self/mounts`); `test_a_var_tmp_directory_not_ours_is_refused` (a link, another owner, mode 0755); `test_a_recorded_home_is_kept`; `test_our_network_filesystems_are_d2s`; `test_setup_state_round_trips_and_writes_atomically` |
| `tests/app/test_runtime.py` | `test_a_first_launch_checks_then_installs_from_the_lock`; `test_a_relaunch_with_nothing_changed_runs_no_uv_and_no_git`; `test_a_new_commit_or_lock_reinstalls`; `test_a_broken_runtime_python_reinstalls`; `test_an_unreadable_deep_reasoner_installs_nothing` (exit 10, `no_access_dr`); `test_a_failed_install_keeps_current_and_exits_11`; `test_an_interrupted_install_is_cleaned_up`; `test_git_never_prompts` (the environment); `test_the_runtime_lock_matches_uv_lock` (runs `uv export`); *(v2)* `test_a_background_child_that_keeps_the_output_never_holds_setup` (`run_logged` returns within `PUMP_DRAIN_S` of its process's exit while a `sh -c "sleep 30 &"` grandchild still holds the pipe); `test_nothing_setup_starts_leaves_the_process_group` |
| `tests/app/test_profile.py` | `test_the_profile_is_created_and_made_the_default_once`; `test_a_relaunch_writes_nothing`; `test_the_users_spend_cap_and_other_arguments_survive`; `test_the_profile_always_turns_sub_agent_sessions_on` (*v2*, in place of v1's flat-fallback test); `test_a_refused_profile_fails_setup_with_exit_12`; `test_a_deleted_profile_is_recreated_but_not_reactivated`; `test_a_command_path_with_spaces_is_shell_quoted` |
| `tests/app/test_canvas_app.py` (*v2:* skeleton) | `test_the_backend_artifact_is_byte_for_byte_stable`; `test_the_manifest_names_both_architectures_and_the_home`; *(v2)* `test_only_the_apps_own_files_are_staged` (a changed `ui/` file leaves the digest alone); *(v2)* `test_our_app_name_is_d3s`; `test_a_first_install_enables_approves_and_starts`; `test_a_relaunch_only_starts_the_backend`; `test_an_upgrade_stops_reinstalls_and_reapproves`; `test_a_disabled_app_is_left_alone`; `test_an_agent_server_refusal_warns_and_setup_succeeds`; and one test against a real agent-server from the SDK fork's pinned commit (marker `crossrepo`) that the staged App installs, its artifact passes `prepare` and the backend answers `/health`. v1's ingress-fallback test is gone (§4.9) |
| `tests/app/test_cli.py` | `test_the_phase_comes_from_the_launchers_variable`; `test_a_hand_run_does_both_phases_when_the_agent_server_is_up`; `test_two_setups_never_run_at_once` (the lock); `test_nothing_secret_is_printed` (the session key absent from stdout); `test_export_runs_the_runtimes_dr_library_with_the_home`; `test_home_records_a_local_folder_and_refuses_a_network_one` |
| `tests/canvas_app/test_notice.py` (D3's) | *(v2, decision O)* `test_the_notice_is_d5s_sentence_with_the_cap` compares with `texts.safety("7")`; it stops skipping once `dr_app` is a dev dependency, in the same commit |
| `tests/app/test_bootstrap.py` | `sh` with stub `git` and `uvx`: `test_no_git_says_how_to_install_it`; `test_an_unreadable_deep_reasoning_says_so_and_keeps_uvx_status`; `test_dr_apps_own_failure_passes_through_without_the_access_line`; `test_the_arguments_reach_dr_app_unchanged` (a path with a space) |

*(v3: as built, the table's names hold but these. `test_runtime.py`:
`test_a_first_launch_checks_then_installs_the_commits_own_lock` and `test_a_new_commit_reinstalls` (renamed, B22);
`test_the_runtime_lock_matches_uv_lock` gone with the file; new,
`test_deep_reasoners_pin_is_read_from_uv_lock_as_pyproject_names_it`,
`test_the_runtimes_uv_sync_reads_no_project_setting_that_changes_its_set` (B22),
`test_the_runtimes_commands_run_from_where_the_install_leaves_them` (B2), `test_without_uv_nothing_is_installed` and
`test_the_runtime_lock_installs_on_every_platform_the_app_ships_for` (B12, it reads PyPI). `test_layout.py`: new,
`test_a_setup_state_this_app_could_not_have_written_says_why`, `test_a_setup_state_that_cannot_be_read_says_why`
(B21), `test_a_home_too_long_for_a_claude_runs_socket_is_refused`,
`test_setup_refuses_a_default_home_too_long_for_a_claude_runs_socket` and
`test_linuxs_limit_is_where_a_socket_stops_binding` (B3). `test_canvas_app.py`: new,
`test_an_unsupported_platform_says_so`; the `crossrepo` one is
`test_the_staged_app_passes_prepare_and_its_backend_answers_health`. `test_cli.py`: new,
`test_a_failed_check_exits_with_its_code_and_its_sentence`,
`test_home_refuses_a_folder_too_long_for_a_claude_runs_socket`,
`test_after_ready_without_the_agent_server_is_a_usage_error`, `test_the_bin_links_lead_to_the_runtime` and
`test_a_setup_state_it_cannot_use_is_explained_and_exits_14` (B21). `test_bootstrap.py`: the second and third are
`test_an_unreachable_deep_reasoning_says_so_and_keeps_uvx_status` and
`test_dr_apps_own_failure_passes_through_without_the_fetch_line` (B15). `tests/app/test_texts.py` compares v2's
sentences with fields. The stubs are scripts in `conftest.py`; the stub `git` lays a copy of this repository's
`uv.lock` into the "fetched" tree; `fake_agent_server.py` answers as the agent-server does. Part 2 and Part 3 of
"Which tests carry which property" map each to its property.)*

### 7.3 The build

`tests/desktop/test_build.py`: `test_pins_with_a_short_commit_are_refused`;
`test_a_canvas_fork_wired_to_another_sdk_commit_is_refused` (the sentence of §6);
*(v2)* `test_a_commit_off_the_forks_deep_reasoning_branch_is_refused` (check 8);
`test_a_typescript_client_from_another_tag_is_refused`; `test_a_different_acp_python_is_refused`;
`test_defaults_gain_only_d5s_four_keys`; `test_telemetry_is_off_in_the_built_defaults`;
`test_the_setup_command_embeds_the_bootstrap_and_the_commit`; `test_a_dirty_or_unpushed_checkout_is_refused`.
`ls_remote`, the SDK file reader and `is_on_branch` are passed in. The packaging itself is tested by building it, in
§7.5 and §7.6. *(v3: twenty tests as built. Beside the above: `test_pins_that_belong_together_pass_every_check`,
`test_a_tag_that_moved_is_refused`, `test_a_fork_that_carries_our_values_is_refused`, the committed pins' two (B12),
`test_a_debs_payload_paths_keep_their_spaces`, and the Mac and machine tests of B14 and B19. The GitHub readers
themselves have no unit test, B24.)*

### 7.4 `fork-live.yml`: S1's and S2's live tiers with `dr-acp` (built)

*(v2: built as v1 wrote it, and on `main` since `633a00d`, so v1's copy of the YAML is dropped here; the file on
`main` is the reference.)* On demand only (it calls gpt-6-luna: cents per run). The run uses the dispatched
branch's copy, and `dr-acp` comes from that same checkout. Run 37147706623, dispatched on `ci/fork-live`
(`a8154e2`: D1's `dr-acp` plus this file) with `sdk_ref` `a3279be`, passed S1's file 2 of 2 and S2's 8 of 8: the
two tiers' Gate B evidence (S1 v2.3, S2 v2.5). The proxy did not exist then. Once step 2 of §1.2 lands, the
Implementer dispatches it on `v1-desktop` with `sdk_ref` `dr-2`, so both tiers run through the key proxy against
the real provider.

- **Inputs:** `sdk_ref` (required), `suites`, `sdk_repo`, `live_config`. deep-reasoning's ref is the ref the run
  is dispatched on (`gh workflow run fork-live.yml --ref v1-desktop -f sdk_ref=dr-2`).
- **Secrets:** `DEEP_REASONER_TOKEN` (the read token D1's CI already uses) and `OPENAI_API_KEY`.
- The two live files and their variables are S1's (§7.4, S1 §5.1 guarantee 10) and S2's (§9). `root` is the
  advising config's non-default namespace (its entry namespace is `advising`). That config offers a decomposition
  only in `advising`, so S2's "the preview equals the started session" check compares options, and an empty command
  list, in `root`; a second namespace with a decomposition in D1's live config would make it compare commands too
  (D1's file, D1's call). With the proxy on by default, the live tier also exercises it against the real provider
  (gpt-6-luna is priced: D1's live test asserts it).

*(v3: dispatched on `v1-desktop` with `sdk_ref` `dr-2` at each revision's head; at `3e9cee9`,
[run 37256842683](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256842683): S1 2 of 2 in 38.8 s,
S2 8 of 8 in 98.8 s, `dr-acp` with the key proxy on, since no flag turns it off. The file is `main`'s, unchanged by
D5's stack.)*

### 7.5 `cross-repo.yml`: pins, E12, E5, E6

Triggers: `pull_request` touching `desktop/**`, `packages/dr-app/**`, `pyproject.toml`, `uv.lock`,
`src/deep_reasoning/acp/proxy.py` or the workflow (D5's own stack, and every pin bump after it, is such a pull
request into `main`; *v2:* v1 said `self-hosted-v1`); `workflow_dispatch` (the copy on `main` lets any branch
dispatch it; the Implementer runs it on `v1-desktop`); and nightly through `main`'s `.github/workflows/nightly.yml`,
which runs on a schedule (`cron: "17 6 * * *"`) with `permissions: actions: write` and does one step,
`gh workflow run cross-repo.yml --ref v1-desktop` (once D5 has merged, `--ref main`). No job calls a real model.
Private access as in D1's CI: `DEEP_REASONER_TOKEN` for DeanLight, and the workflow token, through an `insteadOf`
line, for deep-reasoning itself (the app's setup fetches it like a user's would).

*(v3, B26, B15, as built. The triggers are `pull_request` on the paths above, `workflow_dispatch`, and a schedule of
the file's own, `17 6 * * *`, which GitHub runs only from the default branch: until the stack merges, `main`'s
`nightly.yml` keeps dispatching this file on `v1-desktop`, and #42 deletes `nightly.yml`. There is no `has-d5`. Only
DeanLight needs an `insteadOf` line; deep-reasoning is public. `pins` checks out the commit itself, never a pull
request's merge commit, since check 6 asks that it be on `origin`, and passes `GITHUB_TOKEN` to check 8. The jobs are
the four below; `library-app`'s test runs in `bridge-replay`.)*

| Job | Part | Does |
|---|---|---|
| `pins` | skeleton | `uv run desktop/build.py check` (§4.2.2) |
| `desktop-e2e` | skeleton, grows | E12 on the Linux app (below) |
| `bridge-replay` | skeleton (*v2:* S1 merged; v1 had it final) | E5's second half, `tests/crossrepo/test_bridge_replay.py`: the SDK fork checked out at its pinned commit and synced (`uv sync --frozen`); its agent-server started from that environment; for each of D1's ten `tests/acp/golden/*.native.jsonl`, a conversation whose ACP agent is S1's scripted agent (`[<sdk python>, <sdk>/tests/fixtures/acp/scripted_agent.py, --transcript, <recording>]`, `acp_subagents: true`; S1's player infers the wait points of an outgoing-only recording, S1 §4.10); one message; the stored events' tree (children, parents, spawning cells, cells per session; S1 §5.1 guarantee 2) equals `deep_reasoning.acp.testing.tree()` of the recording. S1's Cartographer replayed nine of them through the bridge in an uncommitted probe, nine equal trees (S1 design, Gate B section), and C1's `1135e87` reports all ten rendering as stored through `dr-1`; this job makes it evidence. |
| `canvas-replay` | final (**C1**) | E6, as C1 §6.4 specifies it: the Canvas fork and the SDK fork checked out at their pinned commits; from the Canvas checkout, `npx playwright test --config=playwright.mock-llm.config.ts tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts` with `OH_ACP_REPLAY_TRANSCRIPTS` = D1's ten native recordings joined with `:`, `SCRIPTED_ACP_AGENT` = `<sdk>/tests/fixtures/acp/scripted_agent.py`, and what the mock-LLM config needs (`npm ci`, `npm run build:app`, Playwright's Chromium, `MOCK_LLM_PYTHON`), set up as the fork's `mock-llm-e2e.yml` does. Each transcript's rendered tree equals its stored tree. |

**E12, `tests/desktop/test_e12.py`** (marker `desktop`; `ubuntu-latest`, about 30 minutes): build with
`uv run desktop/build.py linux`; `sudo apt-get install ./dist/*.deb`; under `xvfb-run`, with `HOME` a fresh
directory (so the first launch is a real one: cold uv cache, nothing installed) holding the runner's `insteadOf`
lines, start `/opt/Deep Reasoning/deep-reasoning --remote-debugging-port=<p>` and attach Playwright over CDP
(`chromium.connect_over_cdp`) to the window on `localhost:8000`. `FakeOpenAI` runs in the test process.

Skeleton flow:
1. The first launch reaches the main window; its stdout (the launcher's log) shows both setup phases, the safety
   line and `agent profile deep_reasoner created and made the default`; `GET …/dr-library/backend` is `ready`
   (*v2:* moved here from the final flow), and `/server_info`'s `app_backend_ingress_url` is
   `http://127.0.0.1:18000` (C3 B2).
2. Set the Canvas secret `OPENAI_API_KEY=sk-e12-<random>` through the REST API (the session key from
   `…/agent-canvas/api-key.txt`); point the Library at the fake with
   `~/.deep-reasoning/runtime/current/bin/dr-library import tests/desktop/e12/main.yaml --home ~/.deep-reasoning`
   and price its model in `~/.deep-reasoning/prices.yaml`.
3. In the window, start a conversation (the default agent is `deep_reasoner`) and ask the scripted question; the
   answer appears.
4. E10 in the real app: the worker's `/proc/<pid>/environ` holds neither the key nor any agent-server secret; the
   fake saw the real key.
5. The App-backend bridge in Electron's own Chromium (§4.9's proof): *(v2)* D3's frame, not a probe App, at
   `ingress_url + "ui/?tab=namespaces&cap=5"` inside the window's `http://localhost:8000`; it shows the notice equal
   to `texts.safety("5")` (`dr-notice`), then, after `dr-notice-ack`, the namespaces step 2 imported
   (`dr-node-<namespace>`); its cookie is partitioned; and after the session is deleted the frame's next request is
   refused.
6. *(v2)* Quit: the app exits within 6 s (C3 v3 §4.4: the launcher in about 4 s, inside Electron's 6 s net), and no
   process of the setup command (`uvx`, `dr-app`, `uv`) is left.
7. Run the setup command's before-start phase alone with the network cut: *(v2, C3 B3)* `unshare --map-root-user
   -n`, then `ip link set lo up`, after `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` on Ubuntu
   24.04, as C3's `launcher-live.yml` does. It exits 0 within 5 s with no `installing` line (the bootstrap's `uvx`
   from its cache, `dr-app` on its cheap path).

Final flow, each part added with the pin bump that brings it (§1.2):
- **C1** (*v2:* C1 v3 §4.12, §9.4; its branch since Gate B): the scripted question spawns sub-agents with
  `run_all`. Each `subagent-row` sits under the `acp-tool-call` that spawned it, with its `subagent-status`. E12 reads
  the nesting with its own Python copy of C1's `expandAllSubagents` and `readRenderedSubagentTree` (A.9: the same
  in-page DOM reads, against SUB-011's ids; `tests/desktop/e12/subagents.py`, about 40 lines, since E12 is Python and
  C1's helpers are TypeScript), and the tree equals the run log's (`deep_reasoning.acp.testing.tree`). Costs are
  hidden by default, so E12 first asserts no `subagent-cost`, then turns on "Show sub-agent costs" on
  `/settings/app` (`show-subagent-costs-switch`, as C1's `showSubagentCosts` does), reloads, and asserts each row's
  latest cost. One `subagent-stop` with `data-subagent-stop="ready"` stops that child and its branch.
- **C2** (C2 v2 §3.2 B15, CX-006 and ASC-005): before the first message, the picker (`agent-options`,
  `agent-option-namespace-value-<namespace>`) and the slash menu (`slash-command-item`, `data-command`) list the
  namespace's decompositions; `conversation-app-panel-toggle-dr-library-decompositions` opens D3's panel at the top
  right, whose frame shows the Library's namespaces through the bridge; Create decomposition (D3's `dr-name`,
  `dr-use-when`, `dr-card-0-task`, `dr-namespace-<namespace>`, `dr-save`, `dr-result`) saves one into that
  namespace; the next conversation there offers it in the slash menu, and its run log's
  `run.start.source.versions` records it (D2, D3); the panel still loads after its first session's five minutes
  (C2's renewal).
- **D4** (D4 §11.4): an MCP server added through Canvas's settings API (D4's `echo_server.py`), ticked for the
  conversation's namespace in the Tools tab (D4 Appendix B's ids), is called by the next conversation's cell.

*(v3, B7: both flows are built as one module of seventeen tests sharing one launch, in file order, on
`ubuntu-24.04` (the job's limit 60 minutes). At `3e9cee9`: the build 4 min 2 s, the `.deb` 150 MB, **17 passed in
416.1 s**, the first launch through both setup phases to the window 32.3 s, the header-panel test 320.5 s since it
outlasts the bridge's five-minute session. The order: the launch (step 1); no consent asked; onboarding keeps
`deep_reasoner` and its hello starts the first conversation (Canvas `dr-3`, which settles §11 item 10); E10 inside
the app (steps 3 and 4); nothing records consent; D3's frame through the bridge (step 5); C1's tree, costs and Stop;
C2's home screen, Create decomposition and the next conversation; D4's Tools tab and MCP server; the header panel past
its first session; the quit (step 6); the offline relaunch (step 7). Where they
differ from the text above: step 2's Library config is written by the test (no `e12/main.yaml`); Stop's plan spawns
the done sibling first and holds the grandchild's call until `dr-acp` logs `stop.accepted` (TASK-38); costs are
compared with the run log's at each sub-agent's end; the next conversation asks a plain question once the slash
menu offers the command; the cookie is read with `Storage.getCookies`; D4's server is added with `POST
/api/settings/mcp/echo` and the Tools tab reopened; the quit asks that no process's command line names the fresh
HOME. The harness is `tests/desktop/app.py`, which the macOS smoke shares; it calls the agent-server through
`dr_app`'s `AgentServer` (B29). E5's job, `bridge-replay`, is 12 tests (D1's ten recordings, the Library App's
`crossrepo` test and D4's forwarding test, B26); E6's, `canvas-replay`, 10 of 10 on C1's replay spec at Canvas
`4355a36`, with TASK-41's race (one run in five) still open in the Canvas fork.)*

### 7.6 `desktop-release.yml`

`push` of a tag `v*` and `workflow_dispatch` (artifacts only). Jobs: `linux` (`ubuntu-latest`: `build.py
linux`, `.AppImage` and `.deb`) and `macos` (`macos-latest`: `build.py mac-universal`, one `.dmg`), each with
§4.2.4's output check. On a tag, a first step requires `cross-repo.yml` green on the tagged commit (`gh run list
--workflow cross-repo.yml --commit <sha> --status success`), and the last attaches the packages to the release
(private, like the repository). The macOS job launches the built app once with a fake model and waits for
`backend ready` in its log, which is S2 PR 3's falsifier on a real Mac ("the Library App's backend does not start
on macOS", S2 §9). *(v2: skeleton, no longer final: D3 and S2's #3 are merged. The first release tag stays final.)*

*(v3, B14, B15, B8, as built. The jobs are `cross-repo-green` (tags only), `linux`, `macos` and `release` (tags
only). `macos` runs `build.py mac-arm64` on `macos-latest` (Apple silicon), copies the `.app` out of the `.dmg`, and
runs `tests/desktop/test_launch_smoke.py` against it: two tests on one launch, the backend `ready` and a clean quit,
and arm64-only Electron and uv; the app's log and macOS's crash reports are kept as an artifact whatever the result.
There is no Intel job. `release` creates the tag's release if it is missing and uploads the packages with `--clobber`;
the downloads are public, like the repository. No `v*` tag exists yet, so the release path has not run. At
`3e9cee9`, [run 37256038987](https://github.com/michaeltheologitis/deep-reasoning/actions/runs/37256038987): `linux`
and `macos` green, the smoke 2 passed in 56.7 s on the `macos-26-arm64` image, before-start `installed in 12s`.)*

---

## 8 · What other designs must change, and what D5 asks of D3, C1 and C2

These are contract findings for the Conductor; none is settled sideways. *(v2: three of v1's asks are met (§8.2,
§8.3, §8.5), one is half met (§8.1), §8.4's are adopted but not merged, and §8.6 is now the redone wiring. §8.7 is
new.)* *(v3: every one is met. §8.1 and §8.7 are built in D5's stack (#37, #40, #42); §8.3's line is in #38; §8.4's
and §8.6's landed in the Canvas fork, B1. Nothing here is owed to another design any more; D1's design names the
tool-client half when it next revises.)*

### 8.1 D1: route tool clients through the seam

*(v2: D1 is merged, `main` at `1f9fe52`. v1's second ask, `OPENHANDS_AUTOMATION_API_KEY` in `ALWAYS_REMOVED`, is
built (D1 B2, `route.py:29–34`, pinned by `test_route.py::test_the_agent_servers_secrets_never_reach_the_worker`).
The tool-client half below is still to build. D5's Implementer builds it, first, in D1's files on `v1-desktop`
(§1.2 step 1), and D1's design names it when it next revises.)*

D1's `ModelRoute` routes the main client only (`RouteGrant.client_overrides` is "merged over `cfg.client`",
`worker/protocol.py:15`, `worker/runner.py:125`). A tool with its own `client` naming the same key (deep_reasoner's
`rag` example does, `configs/example/rag.yaml:25–27`) would then either keep the key in the worker or, once the
proxy removes it, fail. The change is additive; every default keeps D1's behaviour and tests:

```python
@dataclass(frozen=True)
class RunSource:
    config_path: Path
    namespace: str
    client: Mapping[str, Any]
    versions: Mapping[str, Any]
    # NEW: tool name -> its own client block as loaded, for tools that have one.
    tool_clients: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class RouteGrant:
    client_overrides: Mapping[str, Any] = field(default_factory=dict)
    env_add: Mapping[str, str] = field(default_factory=dict)
    env_remove: frozenset[str] = frozenset()
    # NEW: tool name -> overrides merged over that tool's client block.
    tool_client_overrides: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


class ModelRoute(Protocol):
    def grant(
        self,
        *,
        session: str,
        run: str,
        upstream: Mapping[str, Any],
        tool_upstreams: Mapping[str, Mapping[str, Any]] = ...,  # NEW
    ) -> RouteGrant: ...

    def release(
        self,
        run: str,
    ) -> None: ...


class Start(BaseModel):
    ...  # D1's fields
    tool_client_overrides: dict[str, dict[str, Any]] = {}  # NEW
```

- `ConfigCatalog.materialize` (`acp/catalog.py`) fills `tool_clients` (every `cfg.tools[name]["client"]` that is a
  mapping; `tools` is `dict[str, dict[str, Any]]`, deep_reasoner `config.py:426`). D2's `LibraryCatalog` gets it for
  free, since it delegates `RunSource` to `ConfigCatalog` (`library/catalog.py`, its `materialize`).
- `RunHandle.start` (`supervisor.py:133–143`) passes `tool_upstreams=source.tool_clients` and sends the overrides in
  `Start`; the worker merges each into `cfg.tools[name]["client"]` right after it merges `client_overrides`
  (`worker/runner.py:125`).
- `DirectRoute.grant` accepts and ignores `tool_upstreams`.
- `cli.py` gains §5.7's two options and builds the proxy (D5's Implementer edits D1's file, as D2's did).
- D4 adds its own field to `Start` (`mcp_servers`, D4 §11.1); the two are independent, and `v1-desktop` merges
  `main` once D4 is on it.

About 25 lines in D1's files, plus their tests. *(v3: built as written, in #37 (`f106a0c`): +128 net lines in D1's
files with the options and the proxy's construction, +114 of tests. `DirectRoute` and `ProxyRoute` default
`tool_upstreams` to `route.NO_TOOL_UPSTREAMS`, an empty `MappingProxyType`; the worker's merge is
`worker/runner.py`'s `run_config(start)`.)*

### 8.2 S1: the opt-in on the agent profile (met)

*(v2: built as asked, SDK #13: `ACPAgentProfile.acp_subagents: bool = False` (`profiles/agent_profile.py:292`),
forwarded by the resolver (`resolver.py:305`) and carried back by the seed (`seed.py:58`), with a v2 profile
baseline (`tests/sdk/persisted_settings_baselines/v2/agent_profile_acp_subagents.json`); S1 §5.1 guarantee 8. So
setup always writes `acp_subagents: true`, a field it owns, and v1's fallback for an agent-server without it is
gone (§4.5.1).)* v1's text, for the record: Canvas starts every conversation from the active agent profile
(`use-create-conversation.ts:121`), the resolver builds the settings from `ACPAgentProfile`'s fields only, and
`ACPAgentProfile` forbids unknown keys, so without the field no profile could turn the opt-in on.

### 8.3 D3: settled, and what D5 owes it

*(v2: rewritten. v1 proposed four things before D3 was designed; D3 accepted all four (D3 §8.4) and they are
merged.)* The built App ships in the wheel under `deep_reasoning/canvas_app/` and a CI check (`ci.yml`'s
`canvas-app` job) fails if the committed build differs from a fresh one; the panel shows the safety notice the first
time it opens and permanently in its Tools tab, the cap read from the profile; the panel restarts a backend that
died, by `start` of the prepared revision only. What D5 owes D3, D3 §8.4's seven items, each with where D5 does it:

1. Stage only `canvas-extension.json` (with the `backend` block), `dist/index.js` and `panel.svg`: §4.6 step 1,
   `STAGED_FILES`, `test_only_the_apps_own_files_are_staged`.
2. Keep the backend's argv `serve --port {port} --home <DR_HOME>`: §4.6 step 3.
3. The App ingress configured: C3's default (§4.9); nothing of D5's.
4. Approve and start the backend at every launch: §4.6 step 5.
5. `--spend-cap-usd` and `--no-key-proxy` as separate entries of `acp_args`: §4.5.1's table.
6. E12's final flow through D3's selectors (D3 Appendix A.5): §7.5; *(v2)* the skeleton's step 5 already reads
   `dr-notice`, `dr-notice-ack` and `dr-node-<namespace>` in the real app.
7. D5's sentence and D3's stay equal: D3's `test_the_notice_is_d5s_sentence_with_the_cap` calls
   `texts.SAFETY.format(cap=7)`, which assumed a template (D3 B19). D5's `texts.safety(cap)` is a function
   (decision O), so D5's Implementer changes that one line to `texts.safety("7")` in the commit that makes `dr_app` a
   dev dependency, when the test stops skipping. *(v3: done, in #38.)*

### 8.4 C1 and C2: adopted, not merged

*(v2: both adopted what v1 asked; neither is merged.)*
- **C1** (PR #4; C1 v3 §4.12, §6.4, §9.4, A.9): the replay spec
  `tests/e2e/mock-llm/conversations/mock-llm-acp-replay.spec.ts`, one test per path in `OH_ACP_REPLAY_TRANSCRIPTS`
  (D5's name, adopted; skipped when unset), comparing `readRenderedSubagentTree(page)` with
  `readStoredSubagentTree(request, id)`; the SUB-011 test ids (`acp-tool-call`, `subagent-block`, `subagent-row`,
  `subagent-status`, `subagent-cost`, `subagent-stop`, …, listed in the fork's `specs/acp-subagent-sessions.md`); the
  helpers `expandAllSubagents` and `readRenderedSubagentTree` (`tests/e2e/mock-llm/utils/acp-subagents.ts`), which
  E12 mirrors in Python (§7.5); and, since Gate B, "Show sub-agent costs" (frontend-only, in App settings, off by
  default; its switch `show-subagent-costs-switch` is in SUB-011), so E12 turns it on before it asserts a cost. D5
  needs these unchanged when C1 merges; a renamed id or helper is a finding for both.
- **C2** (PR #3; C2 v2 §3.2 B15): the CX-006 ids (`conversation-app-panel-toggle-<extension>-<panel>`,
  `conversation-app-panel-tab-<tab>`, `conversation-app-panel-content`) and the ASC-005 ids (`agent-options`,
  `agent-option-<id>`, `agent-option-<id>-value-<value>`, `slash-command-item` with `data-command`,
  `slash-command-hint`); `host.appBackend.mountFrame`, whose frames read the ingress from `/server_info`'s
  `app_backend_ingress_url`. D3's page runs inside C2's frame; D5's E12 drives both.
- Both are built on `wiring/dr-1` and merge the redone wiring (§8.6) before they merge into the Canvas fork's
  `deep-reasoning`; each merge is followed by a Canvas tag and a pin bump in D5 (§1.2).

*(v3: PR #4 and PR #3 closed unmerged; C1 merged as Canvas #13–#19 and C2 as #20–#26, on the redone wiring, both in
`dr-2` (`9d050ab`). The ids and helpers E12 relies on held: its C1 and C2 tests pass at `dr-3`, B7.)*

### 8.5 The Canvas fork's launcher: a default App-backend ingress (met)

*(v2: built, as v1 proposed it, by C3's #5 (B2, `scripts/dev-safe.mjs:883–884`, pinned by `dev-safe.test.ts ›
buildAgentServerTelemetryEnv › gives Canvas App backends the agent-server's own loopback origin by default` and
`› an OH_APP_BACKEND_PUBLIC_URL in the environment wins`), after Michael approved it as a scope addition to C3 on
2026-10-03. It merged into the Canvas fork's `deep-reasoning` with C3's stack, not into the fork's `main` and not
upstream; v1's "an upstream-shaped PR of its own" is withdrawn. D5's fallback in setup is gone (§4.9).)* D5 relies
on C3 v3's §4 as written; the `sh -c` form is allowed by C3 §2.5.

D2 (§4.8, §6.1) and S2 (merged) need no change.

### 8.6 The redone wiring: not D5's, but the skeleton's pins wait on it

*(v2: rewritten.)* `wiring/dr-1` (`9881d24`) is three fork-only commits on C3's pre-refactor head `22272d9`,
pinning `dr-1`. It is redone on the Canvas fork's `deep-reasoning` at or after `7c12afb`, C3 merged, as fork-only
commits that merge there and nowhere else (not the fork's `main`, not upstream); C1 and C2 then merge it. **What it
must contain for D5:**

1. **`config/defaults.json` `sources`**: `agentServerGitRepo` = `https://github.com/michaeltheologitis/software-agent-sdk`;
   `agentServerGitRef` = the full commit `dr-2` peels to, `34c540ce0598b20ddf913d51968dd903c1c13b2e`;
   `_agentServerGitRefComment` = `tag dr-2 of michaeltheologitis/software-agent-sdk` (C3 v3 §4.5). D5's checks 1 and
   2 (§4.2.2) compare these with `pins.toml`; check 8 needs `34c540c` on the SDK fork's `deep-reasoning`, which it is.
2. **`package.json`** `@openhands/typescript-client` =
   `https://github.com/michaeltheologitis/software-agent-sdk/releases/download/dr-2/openhands-typescript-client-1.50.1.tgz`,
   with the `package-lock.json` npm writes for it (the tarball's hash). D5's check 3 looks for
   `/releases/download/dr-2/`. The release must exist first: `dr-release.yml` creates it when `dr-2` is pushed, once,
   and never replaces the asset.
3. **`scripts/check-sdk-version-sync.mjs` reading a tarball pin** as its locked version (`32bc76e`, with its test),
   so upstream's version-sync check stays green; `versions.agentServer` stays `1.50.1`, the client's version at
   `34c540c`.
4. **`paths.stateDir` and `setup` left `null`**: D5's check 5; D5's build writes them, the fork carries no value of
   ours. Nor does it set `OH_APP_BACKEND_PUBLIC_URL`: C3's default does.
5. Carried for C1's and C2's sake, not D5's: `9881d24`'s `specs` input on `mock-llm-e2e.yml`, and the `sources` keys
   that C1's `mock-llm-e2e.yml` reads to fetch the SDK fork's fixtures.

**And two things after it, which D5 relies on:**
- **C3's `launcher-live.yml` dispatched with no inputs at the wiring's head**, so it reads `sources`: the SDK fork's
  `34c540c` installs once and relaunches with the network cut on the uv the build bundles (C3 v3 §9 item 6, which asks
  for exactly this re-run); and the mock-LLM suite's 180 s web-server timeout re-checked (C3 v3 §4.5; `69d2a6a`
  measured 35–44 s for `cef3b24`).
- **The Canvas fork's first tag**, `dr-1`, on `deep-reasoning` at the wiring's merge commit (the fork has no tag yet;
  D5's check 1 resolves one, §4.2.1). Who pushes it is the Conductor's call, as `dr-2` is Michael's.

**Files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`, placed
the way `fork-live.yml` (`633a00d`) and `live.yml` were, with Michael's yes.

*(v3: all of it is done. `dr-2` was pushed at `34c540c` and its release carries the tarball. The wiring was redone as
the Canvas fork's #12 (`wiring/dr-2`) and tagged `dr-1` at its merge, `fc87687`; `launcher-live.yml` ran green on
`wiring/dr-2` at `9035f9e` (run 37212550240). The
files on `main` are #34 (`cross-repo.yml` and `nightly.yml`, `b2a74e0`) and #35 (`desktop-release.yml`, `f1ca641`);
they are older than this branch's, and the stack replaces them, B11, B26.)*

### 8.7 D4 (v2)

D4 (design v5 §11.4) asks four things of D5; none needs D5 to change before D4 merges into `main`:
- **E10 with an MCP server bound** (§7.1): D4's `echo_server.py`, granted to the conversation's namespace; the same
  assertions, plus the server's own environment holding only its configured variables and `mcp`'s six.
- **One exception to §2.1's first row**, stated there: a stdio MCP server whose Canvas settings name a provider key
  gets it, by the user's configuration.
- **The profile's `mcp_server_refs: null`** (§4.5.1), which D4 reads to say when a server is left out. Already so.
- **An E12 step** (§7.5's D4 part), and D4's cross-repo forwarding test (D4 §10.6), which runs in `cross-repo.yml`
  beside `bridge-replay` once D4 merges.

D4's optional "check every stored tool after an upgrade" in setup is not taken in v1 (§11 item 18).

*(v3: the four are built: E10 with D4's server, which admits `LC_CTYPE` too (B9); §2.1's exception, stated; the
profile's `mcp_server_refs: null`; and E12's MCP step with D4's forwarding test, which runs in `bridge-replay`'s job,
B26.)*

---

## 9 · What D5 relies on

*(v2: re-pinned. Canvas lines at `7c12afb`, SDK lines at `34c540c`, deep-reasoning lines at `main`'s `1f9fe52`.
Row A6 is gone with §4.9's fallback; rows D3, T1, W1, C1, C2, D4, A7 and R5 are new.)*

*(v3: the pins are now Canvas `4355a36` (`dr-3`) and SDK `34c540c` (`dr-2`, unchanged). Of the Canvas files the rows
cite, only `src/services/telemetry.ts` changed between `7c12afb` and `4355a36` (#28 adds `isTelemetryAvailable`,
`:709–716`, which hides consent where a build cannot report; L4's lines hold), so rows C3 and L1–L5 hold at the pin
as cited, and `config/defaults.json` and `package.json` changed only by the wiring, W1. Rows A1–A7, S1, S2 and T1 are
the SDK fork's, whose pin did not move. The rows marked *expected* landed: W1 as
Canvas #12 (`dr-1`), C1 and C2 as #13–#26 (`dr-2`), D4 on `main` (`53c821b`). L6, unverified in v2, holds: E12's
bridge test. U1 changed with B22: D5 no longer runs `uv pip sync` or `uv export`; it runs `uv venv --relocatable
--managed-python` and `uv sync --frozen --no-dev --no-editable --all-packages` with `UV_PROJECT_ENVIRONMENT`, on the
bundled uv 0.12.23 (E12, the smoke and the as-built's install, §5.4). G1 now also carries B26: `cross-repo.yml`'s own
schedule takes effect only once the file is on the default branch. deep-reasoning's line numbers stay `1f9fe52`'s;
D5's changes to D1's files are §8.1's v3 note.)*

| # | Behaviour relied on | Their code |
|---|---|---|
| C3 | `defaults.json` `paths.stateDir` and `setup` as in C3 v3 §4.1–§4.4: both phases every launch, cwd the state directory, stdin closed, the phase variable, `AGENT_SERVER_URL` and `SESSION_API_KEY` after ready, a non-zero exit stops the launch with the output shown, 15 minutes per phase, the key files beside the state directory; *(v2)* a phase ends when the command's output closes; at a timeout or a quit the command's group is signalled even after the command has exited, SIGKILL at 3 s, given up 1 s later; a quit in about 4 s; `OH_APP_BACKEND_PUBLIC_URL` defaulted (B2) | Canvas fork `deep-reasoning` at `7c12afb`: `scripts/dev-with-automation.mjs` (`runSetupCommand`, `stopService`), `scripts/launcher-defaults.mjs`, `scripts/dev-safe.mjs:883–884` |
| L1 | A packaged app puts the bundled `uv` and Node first on `PATH`, then the OS's (`/usr/bin:/bin:/usr/sbin:/sbin` from Finder) | `electron/main.mjs:103–253` |
| L2 | The ingress serves `http://localhost:8000` and the window loads it | `electron/main.mjs:399` |
| L3 | `electron-builder` resolves `directories.app` and `extraResources` against `--projectDir`; the fork's `afterPack` finds the checkout from its own path; `extraMetadata` reaches the packaged `package.json` | `electron-builder.config.mjs:92–96, 324, 332–336, 348, 398` (unchanged since v1's pin) |
| L4 | `VITE_DO_NOT_TRACK=1` at build time and an empty `telemetry.posthogApiKey` turn off the frontend's, agent-server's and automation's reports | `src/services/telemetry.ts:68–70, 361`; `scripts/dev-safe.mjs:752–790`; `dev-with-automation.mjs:102, 1070–1084` |
| A1 | Agent profiles: `POST /api/agent-profiles/{name}` saves (422 with `loc` for an unknown field), `GET` lists ids and the active pointer, `POST /{id}/activate` sets it; `acp_command` is a shell string split with `shlex`; `secret_refs` null passes every secret; *(v2)* `acp_subagents` on the profile | `agent_profiles_router.py:256–481`; `profiles/agent_profile.py:77–135, 223–300`; `profiles/resolver.py:265–306` |
| A2 | Canvas Apps: install from a local path, disabled; a forced reinstall keeps the enabled state and refuses while any App's backend runs; `prepare` checks the checksum and unpacks; `start` needs the prepared revision; the executable must resolve inside the artifact; the backend gets only the allowed variables and runs in the package directory; a local install's revision is the manifest's hash | `canvas_extensions_router.py:189–242, 299–321, 344–404`; `installed.py`; `backend.py:38–40, 151–159, 251–300, 395–412, 478–540`; `manifest.py:185–255` |
| A3 | The ACP bridge passes its environment and the conversation's secrets to the agent, and masks secrets in ACP output | `acp_agent.py:3299, 3306–3331` |
| A4 | `GET /api/settings/secrets` lists names | `settings_router.py:454` |
| A5 | The App-backend bridge: 503 until `app_backend_public_url` is set; requests judged by their `Host`; the session bootstrap from a loopback `Origin` other than the ingress's; a five-minute `Secure; SameSite=None; Partitioned` HttpOnly cookie, issued over http only to a loopback host; loopback origins allowed with credentials by CORS; *(v2)* `/server_info` reports the ingress | `canvas_extensions/bridge.py:33, 231–244, 296–314, 376–447`; `canvas_extensions_bridge_router.py:32–60`; `config.py:350`; `middleware.py:34–60`; `server_details_router.py:150` |
| A7 | *(v2)* For an ACP server no provider claims (`custom`), the bridge applies every provider's credential rule: `CLAUDE_CODE_OAUTH_TOKEN` present removes `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` (§2.2) | `acp_agent.py:2988–2997, 3035–3058`; `settings/acp_providers.py:537–542` |
| L5 | The window loads Canvas from `http://localhost:8000`; the agent-server listens on 127.0.0.1 at the fixed port 18000 | `electron/main.mjs:399, 742`; `config/defaults.json` `ports.agentServer`; `dev-with-automation.mjs:1126–1132` |
| L6 | Electron's Chromium stores a partitioned third-party cookie set on a credentialed cross-site `fetch` from a loopback page, and sends it from a frame on that site (unverified: E12 step 5 is the proof) | Electron 43 (`package.json:154`) |
| D1 | `ModelRoute`, `RouteGrant`, `worker_env`, `ALWAYS_REMOVED` (four glob patterns), `PriceTable` (`estimate`, `$DR_HOME/prices.yaml`), `Home`, `FakeOpenAI`, the harness; `RunHandle.start` grants and `release` at run end; `--home`; `Options`' five fields | `main` at `1f9fe52`: `acp/route.py:9–58`, `acp/costs.py:61–99`, `acp/runlog.py:172–188`, `acp/supervisor.py:133–143, 228`, `acp/cli.py:18–27`, `acp/testing/fake_model.py`; D1 as-built §4.6 |
| D2 | `dr-library serve --port P --home DIR`, `dr-library export DIR --home DIR` and its output line, `/health`, `NETWORK_FILESYSTEMS`, `LibraryCatalog` as `dr-acp`'s default; *(v2)* the `Host` guard | `library/cli.py`, `library/texts.py:225–229`, `library/api.py:324`, `library/store.py:70–72`, `library/catalog.py`; D2 as-built r2 §2 #1, §4.7 |
| D3 | *(v2)* The App package `deep_reasoning.canvas_app` in the wheel (`canvas-extension.json` without a `backend` block, `dist/index.js`, `panel.svg`, `ui/`; `APP_NAME`); `dr-library serve` serves `/ui/`; the page restarts a dead backend by `start` of the prepared revision, never `prepare`; the notice compares with `texts.safety`; the frame's test ids (D3 Appendix A.5) | `src/deep_reasoning/canvas_app/`, `library/ui.py`, `canvas-app/src/page/backend.ts`, `tests/canvas_app/test_notice.py`; D3 §8.4, as-built r4 §3 |
| S1 | `acp_subagents` on the profile (§8.2); the scripted agent's `--transcript` with inferred wait points; the two live-test files and their variables | SDK `34c540c`; S1 v2.3 §5.1 guarantees 8, 9, 10 |
| S2 | Header panels in the manifest (#4); `darwin-*` backends and loopback never proxied (#3); the live-test file and its variables | SDK `34c540c`; S2 v2.5 §5, §6, §9 |
| T1 | *(v2)* A pushed `dr-N` tag on the SDK fork creates prerelease `dr-N` with `openhands-typescript-client-<version>.tgz`, once, never replaced | SDK `.github/workflows/dr-release.yml` (#18) |
| W1 | *(v2, expected)* The redone wiring's `sources`, client pin and version-sync reading (§8.6), and a Canvas tag at its merge | Canvas fork `deep-reasoning`, after `7c12afb` |
| C1 | *(v2, expected)* `OH_ACP_REPLAY_TRANSCRIPTS` and the replay spec; SUB-011's ids; `expandAllSubagents` and `readRenderedSubagentTree` as in-page DOM reads; `show-subagent-costs-switch`, off by default | Canvas PR #4; C1 v3 §4.12, §6.4, §9.4, A.9; `dfde47e`, `4db661f` |
| C2 | *(v2, expected)* CX-006 and ASC-005's ids; `host.appBackend.mountFrame` reading `app_backend_ingress_url` | Canvas PR #3; C2 v2 §3.2 B15, §6.4 |
| D4 | *(v2, expected)* `echo_server.py` and a grant for E10 with an MCP server; D4 Appendix B's ids; the profile's `mcp_server_refs: null` read | `v1-custom-tools` at `461c3b5`; D4 v5 §10.6, §11.4 |
| R1 | `build_client` reads `api_key_env`, falls back to `OPENAI_API_KEY`, uses `base_url` | deep_reasoner `config.py:90–102, 249–266` |
| R2 | A tool block's own `client` is built with `build_client` | `tools/base.py:150–152, 205–207` |
| R3 | A Claude agent's `claude` process inherits the worker's environment, minus `CLAUDE_CODE*` | `v2/claude_code.py:285–307` |
| R4 | `DR_HOME` means something else to deep_reasoner (its Claude run root), so D5 never sets it | `v2/claude_code.py:262–270` |
| R5 | *(v2)* That `claude` therefore never sees a `CLAUDE_CODE_OAUTH_TOKEN` and runs on the machine's own login (D1's EXP-27) | `v2/claude_code.py:285–307` |
| U1 | uv: a commit-pinned git requirement runs from cache offline; `uv pip sync` installs exactly the listed set; `uv export --no-emit-workspace --no-dev --no-hashes`; `uv venv --managed-python` | uv 0.8.17 (C3 §2.3 measured the first); *(v2)* the first re-proved on 0.12.22 and 0.12.23 by C3's live test; the rest not yet run on 0.12.23 (§11 item 15) |
| U2 | uvicorn does not install signal handlers off the main thread | `uvicorn/server.py`, `capture_signals` (*v2:* read again on 0.54.0, the lock's) |
| G1 | GitHub: an on-demand workflow's file must exist on the default branch and runs from the dispatched ref; a scheduled workflow runs from the default branch; a `workflow_dispatch` sent with the workflow token starts a run | GitHub Actions |

---

## 10 · Size

*(v2: re-estimated. Gone: `fork-live.yml` (built, 70), §4.9's fallback (50), the probe App (60), the flat
fallback (30). Added: `run_logged` (40 with its tests), check 8 (15), the staged-files and app-name pins (10),
E12's Python mirror of C1's two reads (40), E10 with an MCP server (30). The Library App moves into the skeleton.)*

| Part | Code | Tests | Skeleton or final |
|---|---|---|---|
| `desktop/` (pins, `build.py` with its eight checks, wrapper config, bootstrap) | 250 | 125 | skeleton |
| `dr-app`: layout and home 90, runtime with `run_logged` 130, agent-server client 50, profile 55, CLI and texts 100 | 425 | 310 | skeleton |
| `dr-app`: the Library App | 110 | 95 | skeleton (v1: final) |
| The key proxy (server and metering 200, routes and grant 85, ledger 60), `cli.py` 20, D1's seam 25 | 390 | 330 | skeleton |
| Workflows: `cross-repo` 150, `desktop-release` 90, the files on `main` 30 | 270 | — | skeleton, except `canvas-replay` (≈30) |
| E12's harness (skeleton 150, final 130 with the mirror of C1's reads), E5's comparator 70 | — | 350 | skeleton 220, final 130 |
| E10 with an MCP server bound | — | 30 | final |
| **Total** | **≈1.45k** | **≈1.24k** | **≈2.7k, about 9 h at Gate C** |

The spec estimated ≈1.2k with tests and ≈4 h. The difference: the key proxy (≈150 in the spec) covers two
dialects, tool clients, an endpoint allow-list, reservations, a price policy and a persisted ledger, because a cap
without them does not bound spending (decision I); the Library App's staging and approval, which the spec left to
the System Designer; the workflows and the E12 harness, which the spec costed at ≈100 together; and `dr-app`'s
own package. About 2.5k of it is the skeleton; the final part is about 0.2k, all of it tests and one CI job.

*(v3: as built, 6,512 reviewable lines, 2,589 of code and 3,923 of tests, and the README's 161: about 22 h at Gate C.
§3.1's "Size" says where v2's estimate fell short.)*

---

## 11 · Open items, and what I was unsure about

*(v3: where v2's items stand at `3e9cee9`. 1: built, #37. 2: done, B1. 3: stands; the Claude CLI behind the proxy is
still unverified, and a `claude` on its own login still escapes the proxy and the cap. 4: the smoke ran on GitHub's
`macos-26-arm64` image only; nothing ran on macOS 14 or on a Mac of ours, and the system-proxy export is unit-tested
only (as-built §7). 5: measured, as-built §5.5: `uvx`'s start for `dr-app` 0.12 s warm, online or not; the first
install 7 s on a Linux machine with a fast network and 12–16 s on the macOS runner, a 474 MB runtime; after-ready 2–4
s. 6: the maintainer is Michael's git identity, his ruling; the icon is still upstream's, and the names a user reads
are TASK-44's, B17. 7: stands. 8: done, #34 and #35, and the stack replaces them, B11, B26. 9: stands, a proposal for
D1's run log. 10: settled by Canvas `dr-3` (#28, #29); E12 goes through onboarding, B7. 11: holds in E12. 12: the
wrapper builds on both platforms. 13: the Canvas tags are `dr-1` to `dr-3`, numbered apart from the SDK fork's. 14:
stands; the one hang seen was the test's own HOME on macOS, B8, and the splash's silence while git waits is TASK-39.
15: answered, the bundled uv 0.12.23 runs D5's commands (E12, the smoke, as-built §5.4). 16: Gate B is done, B13.
17: merged; E12's C1 and C2 tests pass at `dr-3`. 18: stands. Items 19 to 22 are new.)*

1. ~~**S1's profile field** (§8.2)~~ *(v2: met, SDK #13.)* **D1's seam extension** (§8.1): its second half
   (`ALWAYS_REMOVED`) is built; the tool-client half is D5's Implementer's first step, in D1's files (§1.2). The
   Conductor routes it, and D1's design names it when it next revises.
2. **The redone wiring and the Canvas tag** (§8.6) *(v2: replaces v1's "no owner")*: the Conductor's next step after
   `dr-2`. Skeleton step 7 waits on both, and on nothing else.
3. **The Claude CLI behind the proxy** is designed (§4.7.2 step 3) but not verified: I may not run the real
   `claude`, and I do not know every endpoint it calls with an API key (only `v1/messages` and its token count are
   allowed). Whether it matters waits on Dean's answer about the default backbone; so does whether setup installs
   the CLI. If it does: `npm install --prefix ~/.deep-reasoning/runtime/<commit>/node @anthropic-ai/claude-code@<pin>`
   with the bundled npm, linked into the runtime's `bin/` (deep_reasoner puts its interpreter's directory on the
   Claude process's `PATH`, `v2/claude_code.py:298–300`); about 30 lines and a live check. *(v2)* And a `claude`
   on a subscription login escapes the proxy and the cap entirely (§2.2: deep_reasoner drops `CLAUDE_CODE*`, and the
   bridge drops `ANTHROPIC_API_KEY` when `CLAUDE_CODE_OAUTH_TOKEN` is a secret); D5 does not try to route it.
4. **macOS is unverified on hardware:** the system-proxy handling (§4.7.2 step 5), the credential helpers on a
   Finder `PATH`, and the App backend through S2's #3. The release job's macOS smoke (§7.6; *v2:* now in the
   skeleton) is where they are first seen together.
5. **Measured later, in the as-built:** `uvx`'s start for `dr-app` on a relaunch (C3 measured 6.4 s for the
   agent-server's four packages; a package with no dependencies should be far less), the first install's time and
   disk use, and the after-ready cost of starting the backend (D2 measured ≈1.4 s of imports).
6. **The icon and the `.deb` maintainer** are Michael's: the app keeps upstream's OpenHands icon (replacing it is
   three files and one `directories.buildResources` line in the wrapper), and fpm needs a maintainer's email.
7. **`/var/tmp` on a network home** may be cleaned by systemd-tmpfiles after 30 days of disuse; the message says
   so, and `dr-app home` lets the user choose a local folder, but nothing stops the cleanup.
8. **The files on `main`** (decision M): copies of `cross-repo.yml` and `desktop-release.yml`, and `nightly.yml`,
   placed with Michael's yes as `fork-live.yml` was (`633a00d`).
9. **Masking held keys in our own run log** (§2.2): the front knows every value the proxy holds and could replace
   it in what it writes, as the agent-server does in its transcript. That is D1's encoder and run log, so it is a
   proposal, not part of this design; it protects only against a cell that prints a key it found, not one that
   encodes it.
10. **E12's first launch** may meet Canvas onboarding dialogs (an LLM setup prompt for the OpenHands agent, the
    telemetry consent); the harness dismisses whatever appears, and stable test ids (§8.4) would make that
    sturdier.
11. **The App-backend ingress in Electron's Chromium** (§4.9) *(v2: C3's part is settled, built and approved.)* That
    Electron's Chromium keeps the bridge's partitioned cookie for a frame on `127.0.0.1` under a `localhost` window
    is unverified until E12 step 5 runs; so are the bridge's forwarding past D2's `Host` guard (D2 as-built §7 item
    1) and D3's frame behind the real bridge (D3 as-built §9 item 1), which the same step is first to run. If the
    cookie fails, the candidates are the same site on another port (`http://localhost:18000`, weaker isolation,
    decision N) or an https ingress, and the choice comes back here and to C3.
12. **The wrapper config** relies on electron-builder accepting a `.mjs` config outside the project directory with a
    top-level `await import`; electron-builder loads ES module configs, but the build's first run is the check.
13. *(v2)* **The Canvas fork has no tag.** Its first, `dr-1`, is cut at the redone wiring's merge (§8.6), and the
    two forks number their tags apart (§4.2.1). If Michael prefers matched numbers (Canvas `dr-2` for SDK `dr-2`),
    only `pins.toml`'s value changes.
14. *(v2)* **A background process can hold a phase open** (C3 v3 §4.2). Everything `dr-app` starts goes through
    `run_logged` (decision P), but `uvx`'s own fetch of `dr-app` (a first launch, an update) inherits the launcher's
    output. A git credential helper that daemonizes and keeps stderr would hold before-start until the 15-minute
    limit and fail the launch. Git's own `cache` helper and ssh's `ControlPersist` master are, as far as I know, written
    to drop their output when they detach; I did not check either here. If a helper is found that keeps it, the
    bootstrap would need a pipe of its own around `uvx`, which `sh` cannot give without waiting on it.
15. *(v2)* **uv 0.12.23** is pinned for the build because C3's live test proved the offline relaunch on it; D5's own
    uv commands (`uv venv --managed-python`, `uv pip sync` of the export, `uv export --no-emit-workspace`) were read
    against 0.8.17 and are not yet run on 0.12.23. §7.2's runtime tests run the real `uv export`, and the first E12
    runs the rest.
16. *(v2)* **For Michael's Gate B: the departures from the spec**, all in §3: items 1 to 15 stand (13 to 15 with v2
    notes), and 16 is withdrawn (C3's scope addition). v2 adds no departure from the spec. It does make choices Gate
    B may want to see: the skeleton now holds the Library App, E5's replay and the macOS smoke (§1.2); the flat
    fallback is gone, so an agent-server without S1 fails setup (§4.5.1); a line of D3's test changes with
    `texts.safety` (decision O); the build refuses a pin off a fork's `deep-reasoning` (check 8); uv is pinned at
    0.12.23 (item 15); and the size is ≈2.7k, about 9 h at Gate C, against the spec's ≈1.2k and ≈4 h (§10).
17. *(v2)* **C1's and C2's ids may still move.** C1 is being refactored and C2 split; E12's final steps are written
    against SUB-011, CX-006 and ASC-005 as their designs list them, and follow whatever merges (§8.4).
18. *(v2)* **D4's "check every stored tool after an upgrade"** (D4 §14 item 4) is not taken: it would put
    deep_reasoner's imports and every tool's factory on setup's path after each update, and Check already runs
    when a tool is saved. The Conductor may route it to D4's next revision.
19. *(v3)* **Checks 4 and 8 read GitHub, and nothing tests their readers** (B24; as-built §1.3 #6). `read_file_at` and
    `is_on_branch` run only in builds, the `pins` job and the as-built's probes, where both pins pass, and two commits
    off their branches and one that does not exist are refused. An HTTP error other than check 8's 404, such as
    GitHub's limit of 60 unauthenticated requests an hour, is not a sentence: `build.py` ends in a traceback. A local
    `build.py check` without `GITHUB_TOKEN` can meet it. A test with a fake opener and one sentence for an unreadable
    fork would close it, about 30 lines; for the Conductor to route.
20. *(v3)* **No test pins `bad_body`, or that bodies pass uncompressed** (B5). Both are in the proxy's request path; a
    unit test each, in `test_key_proxy.py`, about 25 lines.
21. *(v3)* **Open tasks D5's runs found, none of which blocks D5:** TASK-38 (D1: whether `run_all`'s children progress
    while one child's model call waits; E12 spawns the done sibling first); TASK-39 (the splash says nothing while
    setup waits on a git credential prompt; the README tells the user what to run); TASK-41 (C1's replay spec reads
    the DOM once and fails about one run in five; the as-built r3 cites it as TASK-40, which is r3con's row); TASK-49
    (D1's golden recordings embed CPython 3.12.3's stdlib line numbers, so they fail on 3.12.15; CI runs 3.12.3);
    TASK-46 (the agent-server's auto-title error on a first message, in the UX round).
22. *(v3)* **For Michael at Gate C: one approved behaviour moved** (B23). Offline with no current runtime, setup now
    fails naming `git fetch`, exit 11, where Gate B's build said `no_access_dr`, exit 10. This design takes the new
    order as built; a ruling the other way means checking deep_reasoner's readability before the fetch, which needs
    its URL from somewhere other than the fetched `uv.lock`.
