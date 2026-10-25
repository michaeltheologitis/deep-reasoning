# Deep Reasoning

A minimal chat for Dean's `deep_reasoner`, in one browser tab: your chats on the left, the conversation on the
right, and each run's sub-agents as a tree you click open, in the look of Claude Code.

## Install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), and GitHub access to Dean's private
`DeanLight/deep_reasoner_beta` repository: uv fetches the engine from it with git. If
`git ls-remote https://github.com/DeanLight/deep_reasoner_beta.git` asks for a password, run `gh auth login` and
let it set up git's credentials. Then, from a checkout:

```
git checkout main && git pull
export OPENAI_API_KEY=...
uv run deep-reasoning
```

The first run takes a minute while uv installs everything. It serves on http://127.0.0.1:8000 and opens a tab there;
`--port 8001` picks another port and `--no-browser` skips the tab. Ctrl+C stops it. To bring in a `deep_reasoner`
config first, run `uv run deep-reasoning import path/to/config.yaml` (see [The Library](#the-library)).

Each message runs `deep_reasoner` on the Library's model, with the key in `OPENAI_API_KEY`. The run shows live as a
summary line you click open into its tree of sub-agents, then its answer; Esc or the button in the box stops it.
Every finished run shows its time, its sub-agents and what its model calls cost. Your chats and their runs are kept
in `~/.deep-reasoning`, beside the Library, and come back when you start the app again.

The previous app, a desktop and browser app built on OpenHands, is in this repository's history: its last commit is
`a80bb2e` (`git show a80bb2e:<path>`), and every design doc and as-built is on the `design-docs` branch.

## The Library

Every namespace, decomposition and custom tool your chats draw on, and the run settings, live in one file:
`~/.deep-reasoning/library.sqlite`, made on the first run. A new Library runs chats on gpt-6-luna with the key in
`OPENAI_API_KEY`, under `deep_reasoner`'s generic REPL prompt. To bring in a `deep_reasoner` config, with its
namespaces, their decompositions and the Python files of its tools:

```
uv run deep-reasoning import path/to/config.yaml
```

Items with the same name are replaced. The Library's model and key stay as they are, and its `llm` tools run on them.
A config's top-level decompositions, `dr --main-decomposition` openings, are left out. To share a Library, share the
file; open one with `--library PATH` (on `import` too).
