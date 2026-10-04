"""The live tier (design §7.4): import, edit, version, materialize and run on gpt-6-luna."""

import os
from pathlib import Path

import pytest
import yaml

from deep_reasoning.library import Library, LibraryValidationError, Manifest
from tests.library.conftest import run_dr, text

ADVISING = Path(__file__).parents[2] / "docs" / "configs" / "advising" / "main.yaml"
TASK = "Which course must a student finish before CS102?"
V1_ASK = "Which course comes before STAT102?"
V2_ASK = "What must a first-year student complete before taking STAT102?"
REFUSED_ASK = "Is STAT101 needed for anything?"

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not set"
    ),
]


def first_course(ask: str) -> dict:
    """A worked example over the advising catalog: print the prerequisites, then answer."""
    return {
        "name": "first course",
        "messages": [
            {"role": "user", "content": ask},
            {
                "role": "assistant",
                "content": "<think>The catalog lists each course's prerequisites. I print "
                "them before I answer.</think>\n<repl>\nprint(catalog['STAT102']['prereqs'])\n"
                "</repl>\n",
            },
            {"role": "user", "content": "<observation>\n['STAT101']\n</observation>\n"},
            {
                "role": "assistant",
                "content": "<think>STAT102 needs STAT101.</think>\n<repl>\n"
                "FinalAnswer('STAT101')\n</repl>\n",
            },
        ],
    }


def test_an_edited_decomposition_reaches_a_real_run_at_its_saved_version(tmp_path):
    lib = Library.open(tmp_path / "library.sqlite")
    lib.import_config(ADVISING)
    lib.put_decomposition(
        text(first_course(V1_ASK)), namespaces=["advising"], base_version=0
    )
    lib.put_decomposition(text(first_course(V2_ASK)), base_version=1)
    history = lib.history("decomposition", "first-course")
    assert [h.version for h in history] == [2, 1]
    assert V2_ASK in history[0].yaml and V1_ASK in history[1].yaml

    rev = lib.rev()
    refused = {**first_course(REFUSED_ASK), "use_when": "prerequisites"}
    with pytest.raises(LibraryValidationError) as raised:
        lib.put_decomposition(text(refused))
    assert str(raised.value) == (
        "'first course' is not a valid deep_reasoner Decomposition:\n"
        "  use_when: Extra inputs are not permitted\n"
        "Use-when text is stored beside the YAML: pass use_when=... instead."
    )
    assert lib.rev() == rev

    config = lib.materialize(tmp_path / "config", namespace="advising")
    manifest = Manifest.model_validate(
        yaml.safe_load((config / "library.yaml").read_text())
    )
    assert (manifest.rev, manifest.decompositions["first course"]) == (rev, 2)

    done = run_dr(config / "main.yaml", TASK, cwd=tmp_path)
    assert done.returncode == 0, done.stderr[-2000:]
    assert "CS101" in done.stdout.strip().splitlines()[-1]
    [root_log] = (tmp_path / "runs").glob("*/n_1_d_1_*.yaml")
    logged = root_log.read_text()
    assert V2_ASK in logged
    assert V1_ASK not in logged and REFUSED_ASK not in logged
