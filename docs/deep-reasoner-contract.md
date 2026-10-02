# What deep-reasoning depends on from deep_reasoner

What this app depends on from Dean's `deep_reasoner_beta` (behaviour we build on, and
functionality we need him to add) is tracked as rows in the **Expectations** table in Michael's
Notion, <https://app.notion.com/p/1fb9c801a17046e6888c1ed2b00e2797> (ask Michael for access),
with `From` Dean. Each row says exactly what we rely on, at which commit (`d7334ae` today), and
which part of our design relies on it. From a session in this repo,
`ase-skills expectations list --task 1` lists them, and `ase-skills expectations get EXP-<n>`
prints one.

We do not change deep_reasoner_beta. A branch or PR on Dean's repo happens only if he agrees.

This file used to hold that record. Older references map like this:
- §1.1 (building and running a run) is EXP-3, §1.2 (config shapes) EXP-5, §1.3 (custom tools)
  EXP-6, §1.4 (events) EXP-1, and §1.4's spawning-cell inference EXP-4.
- §1.5 (how we expose deep_reasoner over ACP) is our own design, in the TASK-1 spec.
- Ask A1 (distribution) is EXP-7, and A3 (cancellation) is EXP-2. The other asks, the questions
  for Dean and bugs B1–B8 are not tracked, since nothing of ours depends on them; they are in
  this file's history at `6acd2ea`.
