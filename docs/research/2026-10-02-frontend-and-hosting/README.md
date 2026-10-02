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

The report recommends a custom web app speaking AG-UI, hosted for many users. Discussion on
2026-10-02, including an executive meeting, changed course. Where the report and this list
disagree, follow this list.

1. **A local, single-user app only.** Someone installs it and runs it on their own machine. The
   UW-hosted multi-user website is dropped as a goal, not deferred. Read every hosting section of
   the report as background only.
2. **Build on OpenHands, with deep_reasoner plugged in through ACP.** deep_reasoner runs as an
   ACP agent inside OpenHands (Agent Canvas and the agent-server). This replaces the report's
   custom app and AG-UI.
3. **User experience first, so we fork OpenHands.** The sub-agent tree must be a real tree,
   nested inside the chat, and the decompositions panel must sit next to the chat. Stock
   OpenHands can do neither. A "companion app" beside stock OpenHands was considered and rejected
   because it puts the tree beside the chat instead of inside it. Two forks, under
   `michaeltheologitis/`:
   - `OpenHands/OpenHands`, the Agent Canvas UI;
   - `OpenHands/software-agent-sdk`: the agent-server, the ACP bridge, and the TypeScript client
     Canvas uses.

   Fork rules:
   - Each fork's `main` mirrors upstream.
   - Each change is a generic feature, on its own branch, shaped as an upstream PR. Examples:
     ACP sub-agent sessions, a drawer-tab slot for extensions, forwarding ACP commands and config
     options.
   - Nothing deep_reasoner-specific goes into a fork; that stays in this repo.
4. **ACP is not forked.** Sub-agent sessions, slash commands, config options and cost already
   exist in ACP's upstream schema. Sub-agents are unstable as of 2026-09-30. Anything
   deep_reasoner-specific travels in ACP's `_meta` extension fields. We pin upstream versions and
   fork ACP only for something the protocol cannot express, and even then we propose it to ACP
   as an RFD first.
5. **Sub-agents use ACP's native sub-agent sessions** end to end, not tool calls carrying tree
   data.
6. **Storage, editing and tools.** Decompositions and namespaces are stored in SQLite, with an
   editor. Custom tools are user-written.
7. **deep_reasoner_beta is Dean's repo and stays untouched.** What we depend on from it is
   tracked in the Expectations table that
   [`docs/deep-reasoner-contract.md`](../../deep-reasoner-contract.md) links to.
