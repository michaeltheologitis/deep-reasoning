# Deep Reasoning

A minimal browser chat for Dean's `deep_reasoner` engine, in the look of Claude Code.

## Install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and GitHub access to Dean's private
`DeanLight/deep_reasoner_beta` (if `git ls-remote https://github.com/DeanLight/deep_reasoner_beta.git` asks for a
password, run `gh auth login` and let it set up git's credentials). Then:

```
git clone https://github.com/michaeltheologitis/deep-reasoning.git
cd deep-reasoning
uv run deep-reasoning
```

The first run takes a minute. It opens http://127.0.0.1:8000 in a tab (`--port 8001` for another port,
`--no-browser` for no tab); Ctrl+C stops it, and `git pull` updates it. Then add a key in **settings** (bottom left).

## What it supports

**Chats**
- Chats on the left: new, rename, delete. Saved in the Library file (below), they come back after a restart.
- Each message is a run, shown live as a tree of sub-agents you open level by level. Esc stops it.
- Each run shows its time, sub-agent count, cost (when the price is known) and model.
- Follow-ups see the chat's earlier messages and answers.
- Each chat has its own model, namespace and working folder, picked under the message box; a change applies from
  the next message.
- Light and dark themes; works at phone width.

**Models and keys**, in **settings** (bottom left)
- Vendors and their key variables: OpenAI `OPENAI_API_KEY`, OpenRouter `OPENROUTER_API_KEY`, Anthropic
  `DEEP_REASONING_ANTHROPIC_KEY`, Google Gemini `GEMINI_API_KEY`.
- Custom servers: any OpenAI-compatible URL (vLLM, Ollama, …), with an optional key.
- The model menu shows the current models of each vendor you have a key for, and all of a custom server's; typing
  searches the vendor's full list, and any model name is accepted.
- Keys come from settings or your shell. Settings keeps them in `~/.deep-reasoning/.env`, readable only by you, and
  never shows them again. A saved key wins over the shell's.
- A custom server's key goes only to the address you saved the server with; a server of the same name at another
  address, as in a shared Library file, gets no key until you give it one.
- Runs never read or receive `ANTHROPIC_API_KEY`: Claude Code, as a namespace's backbone or tool, would bill that key
  instead of your Claude subscription.

**Working folders**
- The agent's Python runs in the chat's folder, so files it writes are there for the next message.
- A scratch folder by default, in `~/.deep-reasoning` (hover the folder's name for its path), deleted with the chat.
  A folder you pick is never deleted.
- Settings has a default folder for new chats; one that isn't on this computer gives them a scratch folder.

**The Library**
- One SQLite file of namespaces, decompositions, custom tools and run settings, and your chats and settings:
  `~/.deep-reasoning/library.sqlite`, or another with `--library PATH`. Sharing the file shares all of it but your
  keys, which stay in `.env`, and, for now, the chats' past messages: each file keeps its runs and scratch folders in
  a folder of its own in `~/.deep-reasoning`, so a copy starts without them.
- The **decompositions** panel (top right) adds decompositions as YAML, and adds, edits and deletes namespaces.
- `uv run deep-reasoning import CONFIG.yaml` brings in a `deep_reasoner` config, replacing items with the same name.

The previous app, built on OpenHands, is in history at `a80bb2e`; its design docs are on the `design-docs` branch.
