# deep-reasoning

A minimal chat for `deep_reasoner`, in one browser tab: chats on the left, the conversation on the right, and each run's sub-agents as a tree that clicks open and shut, in the look of Claude Code.

Read `../coding-skills/GUIDE.md` and follow it; in the main session a hook has already printed it.
This project's Notion page (todos, changelog, notes): https://app.notion.com/p/40362fb222378153b3a4edba29ea4329. The brief under its Notes is the whole context for the current work.

## Goals and non-goals

- The UI is agreed: the clickable prototype of PR #73. v1 builds it for real, in five PRs: (1) the app shell; (2) the Library in `library.sqlite`; (3) runs: `deep_reasoner` in a subprocess, steps streamed live, Stop ends the tree, costs per call; (4) chats saved in `chats.sqlite`; (5) the UI wired to real data. Until (5) the chat shows its mock data; the Library panel already shows the real Library.
- The server listens on 127.0.0.1 only, and refuses requests naming another host.
- The Library is one SQLite file (default `~/.deep-reasoning/library.sqlite`, `--library PATH` for another) holding every namespace, decomposition and custom tool's Python source, and the run settings, each as the engine's own YAML. Latest only: sharing or copying the file is the snapshot. `src/deep_reasoning/library.py` is the store; `engine_config()` turns it into the config dict `V2Config` reads at run start. `deep_reasoner` is never changed for it.
- Chats are personal, so they are kept apart from the shareable Library: `chats.sqlite` in the app's home (`~/.deep-reasoning`, beside `runs/`, wherever `--library` points) holds each chat's id, title and when it was made. A chat's turns are its runs, read from `runs/<run>/events.jsonl`, never copied. `src/deep_reasoning/chats.py` is the store.
- No sandboxing or safety layers, and nothing from the old app's OpenHands or ACP stack.

## Checks

- `uv sync`, then `uv run deep-reasoning` serves the app at http://127.0.0.1:8000 and opens a tab (`--port` to change the port, `--no-browser` to skip the tab). `uv run deep-reasoning import CONFIG.yaml` reads an engine config into the Library. The UI is static files in `src/deep_reasoning/web/`, no build step, served at `/`.
- `uv run pytest` (no network: the model is a fake on 127.0.0.1); `uv run ruff check && uv run ruff format --check`; `node --check src/deep_reasoning/web/app.js && node --check src/deep_reasoning/web/library.js` (one file per `node --check`: it ignores the rest).
- `uv run pytest -m live -s` runs the gpt-6-luna live test, a paid call, and logs what it spent; it needs `OPENAI_API_KEY` (in a cloud session `OPENAI_API_KEY=placeholder`: the network proxy adds the real one).
- Check each UI change in a real browser against `uv run deep-reasoning --no-browser` (Playwright is preinstalled in cloud sessions): every chat, a live run, Stop, both themes, phone width, no console errors.
- The chat's mock data in `src/deep_reasoning/web/data/` is generated, never typed: `python3 scripts/mock_from_recordings.py` (the old app's recorded runs → `recordings.json`), `python3 scripts/mock_showcase.py` (the sky, degree and 3,000-essay chats → `showcase.json`; every new message plays back the degree chat).

## Conventions

- No paid model calls except the gpt-6-luna live tests, and the Claude Code on Sonnet live test through Michael's subscription token. Never set `ANTHROPIC_API_KEY`.
- Tests import copies of `deep_reasoner`'s example configs in `tests/configs/` (0.3.0's `docs/configs`, same layout); refresh them from the pinned tag, never edit them.
- Kill only the processes you started: never `pkill -f` or `pgrep -f`.
- `deep_reasoner`'s repository is read-only for us: no PRs, issues or comments there. The app depends on it from GitHub, pinned to a tag in `pyproject.toml`.
- The previous app is in history at `a80bb2e` (`git show a80bb2e:<path>`), and its design docs are on the `design-docs` branch. In a shallow clone, run `git fetch --unshallow` or `git fetch origin design-docs` first.
