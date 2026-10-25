# Deep Reasoning

A minimal chat for Dean's `deep_reasoner`, in one browser tab: your chats on the left, the conversation on the
right, and each run's sub-agents as a tree you click open, in the look of Claude Code.

**Building v1 (2026-10-25).** The UI was agreed on a clickable prototype (PR #73), and v1 now builds it for real.
Until the last of its PRs lands, the app shows the prototype's mock data.

## Install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), and GitHub access to Dean's private
`DeanLight/deep_reasoner_beta` repository: uv fetches the engine from it with git. If
`git ls-remote https://github.com/DeanLight/deep_reasoner_beta.git` asks for a password, run `gh auth login` and
let it set up git's credentials. Then, from a checkout:

```
git checkout main && git pull
uv run deep-reasoning
```

The first run takes a minute while uv installs everything. It serves on http://127.0.0.1:8000 and opens a tab there;
`--port 8001` picks another port and `--no-browser` skips the tab. Ctrl+C stops it.

The previous app, a desktop and browser app built on OpenHands, is in this repository's history: its last commit is
`a80bb2e` (`git show a80bb2e:<path>`), and every design doc and as-built is on the `design-docs` branch.
