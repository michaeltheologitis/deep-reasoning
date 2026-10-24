# deep-reasoning

A minimal chat for `deep_reasoner`, in one browser tab: chats on the left, the conversation on the right, and each run's sub-agents as a tree that clicks open and shut, in the look of Claude Code.

Read `../coding-skills/GUIDE.md` and follow it; in the main session a hook has already printed it.
This project's Notion page (todos, changelog, notes): https://app.notion.com/p/40362fb222378153b3a4edba29ea4329. The brief under its Notes is the whole context for the current work.

## Goals and non-goals

- First, agree the UI with Michael on a clickable prototype he runs on his own machine. Nothing is built before he says the UI is agreed.
- No sandboxing or safety layers, and nothing from the old app's OpenHands or ACP stack.

## Checks

- The prototype is static files in `prototype/` with mock data, no build step. Michael runs it with `python3 -m http.server 8000 --directory prototype`. Check each round in a real browser (Playwright is preinstalled in cloud sessions): every chat, a live run, Stop, both themes, phone width, no console errors.
- The mock data is generated, never typed: `python3 scripts/mock_from_recordings.py` (the old app's recorded runs → `recordings.json`), `python3 scripts/mock_showcase.py` (the sky, degree and 3,000-essay chats → `showcase.json`; every new message plays back the degree chat), `uv run --with pyyaml python scripts/mock_library.py` (deep_reasoner's configs beside this repo → `library.json`, the decompositions panel).
- `node --check prototype/app.js`; `ruff check scripts && ruff format --check scripts`.

## Conventions

- No paid model calls except the gpt-6-luna live tests, and the Claude Code on Sonnet live test through Michael's subscription token. Never set `ANTHROPIC_API_KEY`.
- Kill only the processes you started: never `pkill -f` or `pgrep -f`.
- `deep_reasoner`'s repository is read-only for us: no PRs, issues or comments there.
- The previous app is in history at `a80bb2e` (`git show a80bb2e:<path>`), and its design docs are on the `design-docs` branch. In a shallow clone, run `git fetch --unshallow` or `git fetch origin design-docs` first.
