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
uv run deep-reasoning
```

The first run takes a minute while uv installs everything. It serves on http://127.0.0.1:8000 and opens a tab there;
`--port 8001` picks another port and `--no-browser` skips the tab. Ctrl+C stops it. To bring in a `deep_reasoner`
config first, run `uv run deep-reasoning import path/to/config.yaml` (see [The Library](#the-library)). Then add a
key for a model provider (see [Models and keys](#models-and-keys)).

Each message runs `deep_reasoner` on the chat's model, picked under the message box beside the chat's namespace. The
run shows live as a summary line you click open into its tree of sub-agents, then its answer; Esc or the button in
the box stops it. Every finished run shows its time, its sub-agents, what its model calls cost when the model's price
is known, and its model. Your chats and their runs are kept in `~/.deep-reasoning`, beside the Library, and come back
when you start the app again.

The previous app, a desktop and browser app built on OpenHands, is in this repository's history: its last commit is
`a80bb2e` (`git show a80bb2e:<path>`), and every design doc and as-built is on the `design-docs` branch.

## Models and keys

The app knows four vendors and their addresses, so each takes only a key:

| Vendor | Key variable |
| --- | --- |
| OpenAI | `OPENAI_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Anthropic | `DEEP_REASONING_ANTHROPIC_KEY` |
| Google Gemini | `GEMINI_API_KEY` |

Add a key in any of three ways:

- in the app: **settings**, bottom left, then the vendor's row, paste the key and Save;
- in `~/.deep-reasoning/.env`, as a line like `OPENAI_API_KEY='sk-...'` (the app writes its keys there, readable only
  by you);
- in your shell, as before: `export OPENAI_API_KEY=...` before `uv run deep-reasoning`.

A key in `.env` wins over the same variable in your shell. The app never shows a key again: settings say only `key ✓`
(saved in `.env`), `key from your shell`, or `add key`. Anthropic's key is never read from `ANTHROPIC_API_KEY`, and the
app never hands that variable to a run: Claude Code would bill that key instead of your subscription.

A local or self-hosted server that speaks the OpenAI API (vLLM, SGLang, Ollama, LM Studio, …) is a **custom server**:
in settings, **+ Custom server** takes a name, its base URL (like `http://localhost:8000/v1`) and an optional key,
kept in `.env` as `DEEP_REASONING_<NAME>_KEY`. The servers themselves are listed in `~/.deep-reasoning/settings.json`.

The model menu under the message box lists each keyed vendor's and custom server's own models, and takes any model
name you type. A choice applies from the chat's next message, and the chat keeps it; a new chat starts on the model
picked last, or on OpenAI's `gpt-6-luna` when OpenAI has a key and nothing was picked yet. The namespace menu beside
it works the same way: a new chat starts in the Library's default namespace (★), and you can switch mid-chat.

## Working folders

Each chat works in a folder, shown in the top bar: the agent's Python runs there and reads and writes its files there,
so a file one message writes is there for the next. Click the folder to pick another, by typing a path or browsing; the
change applies from the chat's next message. A chat you don't pick a folder for works in its own scratch folder,
`~/.deep-reasoning/work/<chat>/`, deleted with the chat; a folder you pick is never deleted. **settings** has a
default folder for new chats. Python modules in a chat's folder can be imported, but never in place of an installed
package of the same name.

## The Library

Every namespace, decomposition and custom tool your chats draw on, and the run settings, live in one file:
`~/.deep-reasoning/library.sqlite`, made on the first run with `deep_reasoner`'s generic REPL prompt and a `root`
namespace that grants the `llm` tool, so every namespace has it; an older Library whose `root` is still empty gets
the same when opened. To bring in a `deep_reasoner` config, with its namespaces, their decompositions and the Python
files of its tools:

```
uv run deep-reasoning import path/to/config.yaml
```

Items with the same name are replaced. A config's model and how to reach it are left out: each chat picks its model,
and the Library's `llm` tools run on it.
A config's top-level decompositions, `dr --main-decomposition` openings, are left out. To share a Library, share the
file; open one with `--library PATH` (on `import` too).
