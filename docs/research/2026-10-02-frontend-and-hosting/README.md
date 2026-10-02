# Research: front end and hosting (2026-10-02)

A dated snapshot, not a living document. It was written to answer one question: how should a
web front end for deep_reasoner be built and hosted? Read it as background for the
**TASK-1** spec, not as the plan.

- [`report.md`](report.md): the synthesis.
- [`notes/`](notes): the six research notes it was written from: OpenHands architecture,
  OpenHands hosting, the Agent Client Protocol, alternative UI protocols, bring-your-own-key
  constraints (Claude, Daytona, OpenRouter), and authoring-UX prior art.

Several doc sites were blocked by the network during the research. Claims taken only from
search snippets are marked as such inside the notes.

## Decided after the report: these override it

The report recommends a custom web app speaking AG-UI. Discussion the same day changed course.
Where the report and this list disagree, follow this list.

1. **Self-hosted first.** A UW-hosted, multi-user website is a long-term goal, far in the future,
   and out of scope for v1.
2. **Build on OpenHands, with deep_reasoner plugged in through ACP.** deep_reasoner runs as an
   ACP agent inside OpenHands (Agent Canvas and the agent-server). This replaces the report's
   custom app and AG-UI.
3. **The sub-agent tree must be a real tree, not a flat list.** ACP v2 does not solve this:
   it is a draft, and sub-agents are in its unstable schema. OpenHands' ACP bridge also
   drops update types it does not know. So we change OpenHands: its bridge, and the Canvas
   UI. We carry the change ourselves first and aim to upstream it.
4. **A decompositions panel to the right of the chat.** Decompositions and namespaces are
   stored in SQLite, with an editor. Custom tools are user-written.
5. **deep_reasoner_beta is Dean's repo and stays untouched.** Everything we use from it, and
   everything we need from Dean, is recorded in
   [`docs/deep-reasoner-contract.md`](../../deep-reasoner-contract.md).
