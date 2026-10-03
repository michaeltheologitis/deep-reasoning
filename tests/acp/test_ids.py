import re
from datetime import UTC, datetime

import pytest

from deep_reasoning.acp import ids

RUN = "20261002-142233-4f1a2b"


def test_session_ids_are_s_and_sixteen_hex():
    session = ids.new_session_id()
    assert re.fullmatch(r"s-[0-9a-f]{16}", session)
    assert ids.new_session_id() != session


def test_run_ids_sort_by_start_time():
    run = ids.new_run_id(datetime(2026, 10, 2, 14, 22, 33, tzinfo=UTC))
    assert re.fullmatch(r"20261002-142233-[0-9a-f]{6}", run)


def test_every_id_of_a_run_is_derived_from_it():
    assert ids.child_session_id(RUN, 2) == f"{RUN}-n2"
    assert ids.cell_id(RUN, 2, 1) == f"{RUN}-n2-c1"
    assert ids.card_id(RUN, 2, 1) == f"{RUN}-n2-a1"
    assert ids.task_message_id(RUN, 2, 3) == f"{RUN}-n2-t3"
    assert ids.answer_message_id(RUN, 2, 3) == f"{RUN}-n2-r3"


@pytest.mark.parametrize(
    ("full", "short"),
    [
        ("s-7c1f9e0a2b4d6e8f", "root"),
        (f"{RUN}-n2", "n2"),
        (f"{RUN}-n12-c3", "c12.3"),
        (f"{RUN}-n2-a1", "a2.1"),
        (f"{RUN}-n2-t1", f"{RUN}-n2-t1"),
        ("n3", "n3"),
        ("something else", "something else"),
    ],
)
def test_short_forms_are_for_display_and_leave_other_ids_alone(full, short):
    assert ids.short(full) == short
