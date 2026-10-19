"""What a fresh run is given of its conversation (TASK-57): turns read from run logs, and
the one user message they become."""

import pytest

from deep_reasoning.acp.recap import (
    CUT_MARK,
    NO_RECAP,
    RECAP_HEAD,
    RECAP_MAX_CHARS,
    RECAP_TAIL,
    TEXT_CAP,
    Turn,
    read_turns,
    recap_of,
)
from deep_reasoning.acp.runlog import (
    Home,
    PromptEnd,
    PromptStart,
    RecapNote,
    RunEnd,
    RunLog,
    RunStart,
)


def logged(home: Home, run: str, *events, namespace: str = "root") -> str:
    """A run log: run.start in namespace, then events."""
    log = RunLog.create(home, run)
    log.append(
        RunStart(
            run=run,
            session="s-1",
            index=1,
            after=None,
            cwd="/w",
            namespace=namespace,
            mode="native",
            decomposition=None,
            source={},
        )
    )
    for ev in events:
        log.append(ev)
    return run


def asked(task: str, prompt: int = 1, text: str | None = None) -> PromptStart:
    return PromptStart(prompt=prompt, text=text or task, task=task, decomposition=None)


def prompt_end(outcome, answer=None, detail=None, prompt: int = 1) -> PromptEnd:
    return PromptEnd(prompt=prompt, outcome=outcome, answer=answer, detail=detail)


def run_end(reason, detail=None) -> RunEnd:
    return RunEnd(reason=reason, exit_code=None, detail=detail)


def turn(
    index, message="q", ended="answered", answer="a", namespace="root", detail=None
):
    return Turn(index, namespace, message, ended, answer, detail)


@pytest.mark.parametrize(
    ("events", "line"),
    [
        ([prompt_end("answered", "STAT101")], "Answer 1: STAT101"),
        (
            [prompt_end("exhausted", "still thinking")],
            "Answer 1: (none: the run ended without a final answer)",
        ),
        (
            [prompt_end("failed", detail="ValueError: k"), run_end("failed")],
            "Answer 1: (none: the run failed: ValueError: k)",
        ),
        (
            [prompt_end("build_failed", detail="KeyError: x"), run_end("build_failed")],
            "Answer 1: (none: the run could not start: KeyError: x)",
        ),
        (
            [run_end("stopped")],
            "Answer 1: (none: the user stopped the run before it answered)",
        ),
        (
            [run_end("crashed", detail="/h/runs/r/worker.log")],
            "Answer 1: (none: the run was cut off before it answered)",
        ),
        (
            [run_end("closed")],
            "Answer 1: (none: the run was cut off before it answered)",
        ),
        ([run_end("lost")], "Answer 1: (none: the run was cut off before it answered)"),
        ([], "Answer 1: (none: the run was cut off before it answered)"),
    ],
    ids=[
        "answered",
        "exhausted",
        "failed",
        "build_failed",
        "stopped",
        "crashed",
        "closed",
        "lost",
        "left_open",
    ],
)
def test_a_turn_ends_with_its_answer_or_says_why_it_has_none(tmp_path, events, line):
    home = Home(tmp_path)
    lightest = asked("Which course is lightest?", text="/ask Which course is lightest?")
    run = logged(home, "r1", lightest, *events)
    recap = recap_of(read_turns(home, [run]), "root")
    assert recap.text.splitlines()[2:4] == [
        "Message 1: Which course is lightest?",
        line,
    ]


def test_turns_are_numbered_across_the_runs_of_the_conversation(tmp_path):
    home = Home(tmp_path)
    runs = [
        logged(
            home,
            "r1",
            asked("Plan the term.", prompt=1, text="/plan Plan the term."),
            prompt_end("answered", "planned", prompt=1),
            asked("Now add one.", prompt=2),
            prompt_end("exhausted", "partial", prompt=2),
            run_end("closed"),
        ),
        logged(home, "r2", run_end("closed")),
        logged(home, "r3", asked("Spin."), run_end("stopped"), namespace="math"),
    ]
    assert read_turns(home, runs) == [
        Turn(1, "root", "Plan the term.", "answered", "planned", None),
        Turn(2, "root", "Now add one.", "exhausted", "partial", None),
        Turn(3, "math", "Spin.", "stopped", None, None),
    ]


def test_the_recap_is_one_message_in_the_designs_words():
    recap = recap_of(
        [
            turn(1, "Which course is lightest?", "answered", "STAT101"),
            turn(2, "Spin.", "stopped", None),
        ],
        "root",
    )
    assert recap.text == (
        "This conversation began before this run. Its earlier runs have ended, so their "
        "variables and sub-agents are gone; below are the user's earlier messages, each "
        "with the answer it got.\n"
        "\n"
        "Message 1: Which course is lightest?\n"
        "Answer 1: STAT101\n"
        "\n"
        "Message 2: Spin.\n"
        "Answer 2: (none: the user stopped the run before it answered)\n"
        "\n"
        "The user's next message follows."
    )
    assert recap.note == RecapNote(turns=2, left_out=0, shortened=False)


@pytest.mark.parametrize(
    ("message", "answer", "block", "shortened"),
    [
        (
            "q" * TEXT_CAP,
            "a",
            f"Message 1: {'q' * TEXT_CAP}\nAnswer 1: a",
            False,
        ),
        (
            "q" * (TEXT_CAP + 1),
            "a",
            f"Message 1: {'q' * TEXT_CAP}{CUT_MARK}\nAnswer 1: a",
            True,
        ),
        (
            "q",
            "a" * (TEXT_CAP + 1),
            f"Message 1: q\nAnswer 1: {'a' * TEXT_CAP}{CUT_MARK}",
            True,
        ),
        (
            "q" * (TEXT_CAP - 2) + "   tail",
            "a",
            f"Message 1: {'q' * (TEXT_CAP - 2)}{CUT_MARK}\nAnswer 1: a",
            True,
        ),
    ],
    ids=["at_the_cap", "message_over", "answer_over", "cut_at_spaces"],
)
def test_a_message_or_answer_over_the_cap_is_cut_and_the_note_says_so(
    message, answer, block, shortened
):
    recap = recap_of([turn(1, message, "answered", answer)], "root")
    assert recap.text == f"{RECAP_HEAD}\n\n{block}\n\n{RECAP_TAIL}"
    assert recap.note == RecapNote(turns=1, left_out=0, shortened=shortened)


def sized(index: int, length: int) -> Turn:
    """A turn whose block is length characters (index < 10)."""
    return turn(index, "q" * (length - len(f"Message {index}: \nAnswer {index}: a")))


def test_the_oldest_turns_are_left_out_to_fit_and_the_rest_keep_their_numbers():
    # Turns 2 to 9 fill RECAP_MAX_CHARS exactly, with "\n\n" between them.
    exact = (RECAP_MAX_CHARS - 7 * len("\n\n")) // 8
    fitting = [sized(i, exact) for i in range(2, 9)]
    fitting.append(sized(9, RECAP_MAX_CHARS - 7 * len("\n\n") - 7 * exact))
    recap = recap_of([turn(1), *fitting], "root")
    assert recap.note == RecapNote(turns=8, left_out=1, shortened=False)
    assert recap.text.startswith(
        f"{RECAP_HEAD} Message 1 is left out, to fit.\n\nMessage 2: "
    )

    largest = [turn(i, "q" * 9_000, "answered", "a" * 9_000) for i in range(1, 21)]
    recap = recap_of(largest, "root")
    assert recap.note == RecapNote(turns=3, left_out=17, shortened=True)
    assert recap.text.startswith(
        f"{RECAP_HEAD} Messages 1 to 17 are left out, to fit.\n\nMessage 18: "
    )
    assert recap.text.endswith(f"Answer 20: {'a' * TEXT_CAP}{CUT_MARK}\n\n{RECAP_TAIL}")

    newest = turn(1, "q" * 9_000, "answered", "a" * 9_000, namespace="math")
    assert recap_of([newest], "root").note == RecapNote(
        turns=1, left_out=0, shortened=True
    )


def test_a_turn_from_another_namespace_names_it():
    recap = recap_of(
        [turn(1, "Add pi.", namespace="math"), turn(2, "And now?")], "root"
    )
    assert recap.text.splitlines()[2:6] == [
        "Message 1 (namespace math): Add pi.",
        "Answer 1: a",
        "",
        "Message 2: And now?",
    ]


def test_no_earlier_turns_means_no_recap(tmp_path):
    home = Home(tmp_path)
    closed = logged(home, "r1", run_end("closed"))
    assert read_turns(home, []) == []
    assert recap_of(read_turns(home, [closed]), "root") is NO_RECAP
    assert NO_RECAP.text is None and NO_RECAP.note is None
