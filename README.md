# Deep Reasoning

A minimal browser chat for Dean's `deep_reasoner` engine, in the look of Claude Code.

## Install and run

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and GitHub access to Dean's private
`DeanLight/deep_reasoner_beta` (if `git ls-remote https://github.com/DeanLight/deep_reasoner_beta.git` asks for a
password, run `gh auth login`). Then, from a checkout:

```
git checkout main && git pull
uv run deep-reasoning
```

The first run takes a minute. It opens http://127.0.0.1:8000 in a tab (`--port 8001` for another port,
`--no-browser` for no tab); Ctrl+C stops it.

## What it supports

**Chats**
- Chats on the left: new, rename, delete. Saved in `~/.deep-reasoning`, they come back after a restart.
- Each message is a run, shown live as a tree of sub-agents you open level by level. Esc stops it.
- Each run shows its time, sub-agent count, cost (when the price is known) and model.
- Follow-ups see the chat's earlier messages and answers.
- Each chat has its own model, namespace and working folder, picked under the message box and switchable mid-chat.
- Light and dark themes; works at phone width.

**Models and keys**, in **settings** (bottom left)
- Vendors and their key variables: OpenAI `OPENAI_API_KEY`, OpenRouter `OPENROUTER_API_KEY`, Anthropic
  `DEEP_REASONING_ANTHROPIC_KEY`, Google Gemini `GEMINI_API_KEY`.
- Custom servers: any OpenAI-compatible URL (vLLM, Ollama, …), with an optional key.
- The model menu lists each vendor's current models; typing searches its full list and accepts any name.
- Keys come from settings or your shell. Settings keeps them in `~/.deep-reasoning/.env`, readable only by you, and
  never shows them again. A saved key wins over the shell's.
- Anthropic's key is never read from `ANTHROPIC_API_KEY`: Claude Code would bill that key instead of your subscription.

**Working folders**
- A chat's Python reads and writes files in its folder, so they carry over between messages.
- A scratch folder by default, deleted with the chat. A folder you pick is never deleted.
- Settings has a default folder for new chats.

**The Library**
- One SQLite file of namespaces, decompositions, custom tools and run settings: `~/.deep-reasoning/library.sqlite`,
  or another with `--library PATH`. Share it by sharing the file.
- The **decompositions** panel (top right) adds decompositions as YAML, and adds, edits and deletes namespaces.
- `uv run deep-reasoning import CONFIG.yaml` brings in a `deep_reasoner` config, replacing items with the same name.

The previous app, built on OpenHands, is in history at `a80bb2e`; its design docs are on the `design-docs` branch.
