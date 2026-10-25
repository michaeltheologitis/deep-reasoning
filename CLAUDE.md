# deep-reasoning

A minimal chat for `deep_reasoner`, in one browser tab: chats on the left, the conversation on the right, and each run's sub-agents as a tree that clicks open and shut, in the look of Claude Code.

Read `../coding-skills/GUIDE.md` and follow it; in the main session a hook has already printed it.
This project's Notion page (todos, changelog, notes): https://app.notion.com/p/40362fb222378153b3a4edba29ea4329. The brief under its Notes is the whole context for the current work.

## Goals and non-goals

- The UI is agreed: the clickable prototype of PR #73. v1 built it for real, in five PRs: (1) the app shell; (2) the Library in `library.sqlite`; (3) runs: `deep_reasoner` in a subprocess, steps streamed live, Stop ends the tree, costs per call; (4) chats saved in `chats.sqlite`; (5) the UI wired to real data.
- The page reads chats and runs from the API. `src/deep_reasoning/web/fold.js` folds a run's events into the tree the chat draws, the same for a saved turn and a live one; a live run streams over SSE from `?after=` the last seq the page has, so a reload catches up without gaps or repeats.
- The server listens on 127.0.0.1 only, and refuses requests naming another host.
- The Library is one SQLite file (default `~/.deep-reasoning/library.sqlite`, `--library PATH` for another) holding every namespace, decomposition and custom tool's Python source, and the run settings, each as the engine's own YAML. Latest only: sharing or copying the file is the snapshot. `src/deep_reasoning/library.py` is the store; `engine_config()` turns it into the config dict `V2Config` reads at run start. `deep_reasoner` is never changed for it.
- Chats are personal, so they are kept apart from the shareable Library: `chats.sqlite` in the app's home (`~/.deep-reasoning`, beside `runs/`, wherever `--library` points) holds each chat's id, title and when it was made. A chat's turns are its runs, read from `runs/<run>/events.jsonl`, never copied. `src/deep_reasoning/chats.py` is the store.
- No sandboxing or safety layers, and nothing from the old app's OpenHands or ACP stack.

## Checks

- `uv sync`, then `uv run deep-reasoning` serves the app at http://127.0.0.1:8000 and opens a tab (`--port` to change the port, `--no-browser` to skip the tab). `uv run deep-reasoning import CONFIG.yaml` reads an engine config into the Library. The UI is static files in `src/deep_reasoning/web/`, no build step, served at `/`.
- `uv run pytest` (no network: the model is a fake on 127.0.0.1); `node --test tests/*.test.mjs` (the fold, no dependencies); `uv run ruff check && uv run ruff format --check`; `node --check` on each of `src/deep_reasoning/web/app.js`, `fold.js` and `library.js` (one file per `node --check`: it ignores the rest).
- `uv run pytest -m live -s` runs the gpt-6-luna live test, a paid call, and logs what it spent; it needs `OPENAI_API_KEY` (in a cloud session `OPENAI_API_KEY=placeholder`: the network proxy adds the real one).
- Check each UI change in a real browser against `uv run deep-reasoning --no-browser` (Playwright is preinstalled in cloud sessions): a new chat, a live run with its tree opened, a follow-up, a reload mid-run, Stop, rename, delete, a restart, both themes, phone width, no console errors.
- To drive the UI without a paid model: serve `tests/fake_model.py`'s `FakeOpenAI` from a process of its own on a scripted plan (`scripts/record_runs.py` has fan-outs, nested delegation and a run to stop), set a scratch Library's `client` run setting to its `base_url` as `library_on` in `tests/conftest.py` does, then run `HOME=<tmp> OPENAI_API_KEY=fake uv run deep-reasoning --no-browser --library <tmp>/lib.sqlite`. `HOME` keeps its chats and runs out of your own `~/.deep-reasoning`.
- The fold's fixtures in `tests/runs/` are real runs against the fake model, recorded, never typed: `uv run python scripts/record_runs.py`. Record them again when the worker's events change.

## Conventions

- No paid model calls except the gpt-6-luna live tests, and the Claude Code on Sonnet live test through Michael's subscription token. Never set `ANTHROPIC_API_KEY`.
- Tests import copies of `deep_reasoner`'s example configs in `tests/configs/` (0.3.0's `docs/configs`, same layout); refresh them from the pinned tag, never edit them.
- Kill only the processes you started: never `pkill -f` or `pgrep -f`.
- `deep_reasoner`'s repository is read-only for us: no PRs, issues or comments there. The app depends on it from GitHub, pinned to a tag in `pyproject.toml`.
- The previous app is in history at `a80bb2e` (`git show a80bb2e:<path>`), and its design docs are on the `design-docs` branch. In a shallow clone, run `git fetch --unshallow` or `git fetch origin design-docs` first.
