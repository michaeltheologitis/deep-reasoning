"""Stop on one sub-agent: its branch stops at its next turn, through the interim and
through (a fake of) Dean's stop(node_id) (E3, §6.3)."""

import traceback

import pytest

from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.worker.recorder import EventSink, Recorder
from deep_reasoning.acp.worker.stop import (
    DeanStop,
    InterimStop,
    StoppedByUser,
    resolve_stop_adapter,
)


@pytest.mark.parametrize(
    ("branch", "siblings", "sentence"),
    [
        ((), (), "stopped #2."),
        ((4, 5), (), "stopped #2 and its branch (#4, #5)."),
        (
            (4,),
            (3,),
            "stopped #2 and its branch (#4). Its running sibling #3 in this run_all was stopped with it (A3).",
        ),
        (
            (),
            (3, 6),
            "stopped #2. Its running siblings #3, #6 in this run_all were stopped with it (A3).",
        ),
    ],
)
def test_stopped_by_user_says_what_stopped_with_it(branch, siblings, sentence):
    error = StoppedByUser(2, branch, siblings)
    assert str(error) == sentence
    assert (error.target, error.branch, error.siblings) == (2, branch, siblings)


def test_a_cell_shows_stopped_by_user_under_its_qualified_name():
    try:
        raise StoppedByUser(2, (4, 5), ())
    except StoppedByUser:
        last = traceback.format_exc().rstrip().splitlines()[-1]
    assert (
        last
        == "deep_reasoning.acp.worker.stop.StoppedByUser: stopped #2 and its branch (#4, #5)."
    )


def test_the_adapter_is_the_interim_unless_a_stop_api_is_named(tmp_path):
    with open(tmp_path / "events", "wb") as out:
        recorder = Recorder(EventSink(out.fileno()), PriceTable({}))
        assert isinstance(resolve_stop_adapter(recorder, None), InterimStop)
        dean = resolve_stop_adapter(recorder, "builtins:abs")
    assert isinstance(dean, DeanStop)
    assert dean.mode == "dean"
