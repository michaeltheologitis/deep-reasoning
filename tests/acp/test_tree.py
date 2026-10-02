"""tree(): the run rebuilt from the updates alone, and how it is drawn (§8.2)."""

from deep_reasoning.acp.testing.tree import (
    AgentNode,
    CellNode,
    MessageNode,
    RunNode,
    tree,
)
from tests.acp import streams as s

R3 = "20261002-170000-aaaaaa"


def test_a_native_run_nests_each_child_under_the_cell_that_started_it():
    (run,) = tree(s.native_run()).runs
    n2 = AgentNode(
        session_id=s.N2,
        short="n2",
        node=2,
        drive=1,
        title="Summarize the CS department.",
        outcome="done",
        cost_usd=0.0037,
        items=[
            CellNode(
                f"{s.R1}-n2-c1",
                "c2.1",
                "Run print(cs)",
                "completed",
                "['CS101', 'CS102']",
            )
        ],
    )
    n3 = AgentNode(
        session_id=s.N3,
        short="n3",
        node=3,
        drive=1,
        title="Summarize the STAT department.",
        outcome="failed: ValueError: the catalog has no STAT sec…",
        cost_usd=None,
    )
    assert run == RunNode(
        root_session_id=s.ROOT,
        run=s.R1,
        mode="native",
        cost_usd=0.0089,
        root=AgentNode(
            session_id=s.ROOT,
            short="root",
            node=1,
            drive=1,
            title="",
            outcome=None,
            cost_usd=None,
            items=[
                CellNode(
                    f"{s.R1}-n1-c1",
                    "c1.1",
                    "Run found = run_all(...) …",
                    "completed",
                    "{'CS': 'CS is heavy.'}",
                    [n2, n3],
                ),
                CellNode(
                    f"{s.R1}-n1-c2",
                    "c1.2",
                    "Run FinalAnswer('STAT is lighter.')",
                    "completed",
                    "FinalAnswer: 'STAT is lighter.'",
                ),
                MessageNode(outcome="answered", prompt=1, text="STAT is lighter."),
            ],
        ),
    )


def test_a_tree_is_drawn_one_block_per_run():
    assert str(tree(s.native_run())).splitlines() == (
        [
            "root s-7c1f9e0a2b4d6e8f · run 20261002-162835-3fa9c1 · 0.0089 USD",
            "├─ c1.1  Run found = run_all(...) …  completed → {'CS': 'CS is heavy.'}",
            "│  ├─ n2  Summarize the CS department.  done · 0.0037 USD",
            "│  │  └─ c2.1  Run print(cs)  completed → ['CS101', 'CS102']",
            "│  └─ n3  Summarize the STAT department.  failed: ValueError: the catalog has no STAT sec…",
            "├─ c1.2  Run FinalAnswer('STAT is lighter.')  completed → FinalAnswer: 'STAT is lighter.'",
            "└─ answered  STAT is lighter.",
        ]
    )


def flat_run(run: str) -> list:
    return [
        s.cell(s.ROOT, run, 1, 1, "found = run_all(...)"),
        s.card(run, 2, 1, 1, "Summarize CS.", "#1 › #2"),
        (
            s.ROOT,
            {
                **s.cell(s.ROOT, run, 2, 1, "print(cs)", parent=1)[1],
                "title": "#1 › #2 › Run print(cs)",
            },
        ),
        s.done(s.ROOT, run, 2, 1, "['CS101']"),
        s.card_done(run, 2, "completed", "CS is heavy.", status="done"),
        s.done(s.ROOT, run, 1, 1, "{'CS': 'CS is heavy.'}"),
        s.closing(s.ROOT, run, 1, "answered", "CS."),
        s.usage(s.ROOT, 0.01),
    ]


def test_a_flat_run_draws_each_card_as_its_agent_with_its_labelled_cells():
    (run,) = tree(flat_run(s.R2)).runs
    assert run.mode == "flat"
    (first, _) = run.root.items
    assert first.agents == [
        AgentNode(
            session_id=f"{s.R2}-n2",
            short="n2",
            node=2,
            drive=1,
            title="Summarize CS.",
            outcome="done",
            cost_usd=None,
            items=[
                CellNode(
                    f"{s.R2}-n2-c1",
                    "c2.1",
                    "#1 › #2 › Run print(cs)",
                    "completed",
                    "['CS101']",
                )
            ],
        )
    ]


def test_runs_split_by_conversation_and_by_run_and_drop_what_belongs_to_none():
    other = [
        s.cell(s.OTHER_ROOT, R3, 1, 1, "x = 1"),
        s.closing(s.OTHER_ROOT, R3, 1, "answered", "1"),
        s.usage(s.OTHER_ROOT, None),
    ]
    stream = [
        *s.native_run()[:2],
        *other,
        *s.native_run()[2:],
        s.closing(s.ROOT, None, None, "rejected", "/triage only works first."),
        s.notice(s.ROOT, "Starting a fresh run."),
        *flat_run(s.R2),
    ]
    runs = tree(stream).runs
    assert [(r.root_session_id, r.run, r.mode, r.cost_usd) for r in runs] == [
        (s.ROOT, s.R1, "native", 0.0089),
        (s.OTHER_ROOT, R3, "native", None),
        (s.ROOT, s.R2, "flat", 0.01),
    ]
    assert runs[0] == tree(s.native_run()).runs[0]
    assert [type(i).__name__ for i in runs[2].root.items] == ["CellNode", "MessageNode"]
    assert str(tree(stream)).count("\n\n") == 2


def test_a_child_driven_twice_is_drawn_once_per_drive():
    n2 = s.N2
    stream = [
        s.cell(s.ROOT, s.R1, 1, 1, "a = anext(child.send('one'))"),
        s.announce(s.ROOT, s.R1, 2, 1, 1, "One."),
        s.cell(n2, s.R1, 2, 1, "FinalAnswer(1)", parent=1),
        s.idle(s.ROOT, s.R1, 2, 1, 1, "end_turn", status="done"),
        s.cell(s.ROOT, s.R1, 1, 2, "b = anext(child.send('two'))"),
        s.announce(s.ROOT, s.R1, 2, 1, 2, "Two.", drive=2),
        s.cell(n2, s.R1, 2, 2, "FinalAnswer(2)", parent=1),
        s.idle(s.ROOT, s.R1, 2, 1, 2, "end_turn", status="done", drive=2),
    ]
    first, second = tree(stream).runs[0].root.items
    assert [
        (a.drive, a.title, [c.short for c in a.items])
        for a in first.agents + second.agents
    ] == [
        (1, "One.", ["c2.1"]),
        (2, "Two.", ["c2.2"]),
    ]
    assert "n2 (drive 2)  Two.  done" in str(tree(stream))
