# What deep-reasoning depends on from deep_reasoner

D1's code (`dr-acp`, `src/deep_reasoning/acp/`) relies on Dean's `deep_reasoner_beta`, at the
commit `pyproject.toml` pins. Each thing it relies on is one row of the **Expectations** table in
Michael's Notion, <https://app.notion.com/p/1fb9c801a17046e6888c1ed2b00e2797>: EXP-22 to EXP-48,
which `ase-skills expectations list` prints. A row says whether the behaviour is in place or still
needed from Dean, and points at the code that relies on it by `file:line`. Rows are written when
that code is merged; this file does not copy them.

What this file held before any code existed (the surface we planned to use, asks A1–A7, the
questions for Dean, bugs B1–B8) is in its history at `6acd2ea`.
