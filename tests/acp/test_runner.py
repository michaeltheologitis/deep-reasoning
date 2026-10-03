import pytest

from deep_reasoning.acp.worker.runner import as_text


@pytest.mark.parametrize(
    ("value", "text"),
    [("CS is heavy", "CS is heavy"), (42, "42"), (["a"], "['a']"), (None, "None")],
)
def test_an_answer_is_its_text_or_its_repr(value, text):
    assert as_text(value) == text
