import dataclasses
import subprocess
import sys

import pytest
import yaml

from deep_reasoning.acp.catalog import CommandEntry, ConfigCatalog
from deep_reasoning.library import Library, LibraryCatalog, LibraryNotFound
from tests.library.conftest import example, run_dr, text
from tests.library.fake_openai import FakeOpenAI

ANSWER = '<think>ok</think>\n<repl>\nFinalAnswer("done")\n</repl>'


@pytest.fixture
def catalog(lib, router) -> LibraryCatalog:
    lib.import_config(router)
    lib.put_decomposition(
        text(example("decline")), use_when="off-topic questions", hint="the question"
    )
    return LibraryCatalog(lib.path)


def test_snapshot_equals_config_catalog_over_the_materialized_config_plus_metadata(
    catalog, lib, tmp_path
):
    plain = ConfigCatalog(lib.materialize(tmp_path / "plain") / "main.yaml").snapshot()
    snapshot = catalog.snapshot()
    assert (snapshot.namespaces, snapshot.default_namespace) == (
        ("root", "courses", "router"),
        "router",
    )
    described = CommandEntry(
        "decline", "decline", "off-topic questions", "the question"
    )
    assert snapshot.commands == {
        **plain.commands,
        "router": tuple(
            described if e.decomposition == "decline" else e
            for e in plain.commands["router"]
        ),
    }


def test_commands_carry_use_when_and_hint(catalog):
    router = {e.name: e for e in catalog.snapshot().commands["router"]}
    assert router["decline"] == CommandEntry(
        "decline", "decline", "off-topic questions", "the question"
    )
    assert router["route-a-course-question"] == CommandEntry(
        "route-a-course-question",
        "route a course question",
        "Open with the 'route a course question' decomposition",
        "the task",
    )


def test_a_top_level_decomposition_is_offered_in_every_namespace(catalog, lib):
    lib.put_decomposition(text(example("Triage it!")), top_level=True)
    commands = catalog.snapshot().commands
    assert {ns: entries[0].name for ns, entries in commands.items()} == {
        "root": "triage-it",
        "courses": "triage-it",
        "router": "triage-it",
    }


def test_materialize_gives_d1_a_run_source_with_versions(catalog, lib, tmp_path):
    source = catalog.materialize("courses", run_dir=tmp_path / "run")
    assert source.config_path == tmp_path / "run" / "config" / "main.yaml"
    assert source.namespace == "courses"
    assert (source.client["base_url"], source.client["api_key_env"]) == (
        "http://127.0.0.1:9/v1",
        "FAKE_KEY",
    )
    assert source.versions == {
        "v": 1,
        "library": str(lib.path),
        "rev": 3,
        "namespace": "courses",
        "deep_reasoner": source.versions["deep_reasoner"],
        "profile": 2,
        "namespaces": {"root": 2, "router": 1, "courses": 1},
        "decompositions": {
            "route a course question": 1,
            "decline": 2,
            "catalog lookup": 1,
        },
        "tools": {},
    }
    loaded = yaml.safe_load(source.config_path.read_text())
    assert loaded["entry_namespace"] == "courses"


def test_an_unknown_namespace_is_not_found(catalog, tmp_path):
    with pytest.raises(LibraryNotFound, match="There is no namespace 'gone'"):
        catalog.materialize("gone", run_dir=tmp_path / "run")


def test_a_catalog_creates_its_library_from_the_starter_when_absent(tmp_path):
    catalog = LibraryCatalog(tmp_path / "home" / "library.sqlite")
    assert not (tmp_path / "home").exists()
    snapshot = catalog.snapshot()
    assert (snapshot.namespaces, snapshot.default_namespace) == (("root",), "root")
    assert (
        Library.open(tmp_path / "home" / "library.sqlite").profile().data["model"]
        == "gpt-6-luna"
    )


def test_building_a_catalog_imports_nothing_of_deep_reasoner(tmp_path):
    probe = (
        "import sys\n"
        "from deep_reasoning.library import LibraryCatalog\n"
        f"LibraryCatalog({str(tmp_path / 'library.sqlite')!r})\n"
        "assert 'deep_reasoner' not in sys.modules, sorted(sys.modules)\n"
    )
    subprocess.run([sys.executable, "-c", probe], check=True)


def first_user_messages(request: dict) -> list[str]:
    return [m["content"] for m in request["messages"] if m["role"] == "user"]


def test_a_saved_decomposition_reaches_the_next_conversation_in_its_namespace(
    lib, router, tmp_path
):
    """Design §7.3 below dr-acp's front: what LibraryCatalog hands D1's worker."""
    lib.import_config(router)
    catalog = LibraryCatalog(lib.path)
    with FakeOpenAI(ANSWER) as fake:
        profile = {
            **lib.profile().data,
            "client": {"base_url": fake.base_url, "api_key_env": "FAKE_KEY"},
        }
        lib.put_profile(text(profile))
        lib.put_decomposition(
            text(
                example("summarize then rank", "Summarize each course, then rank them.")
            ),
            namespaces=["router"],
            use_when="comparing many courses",
        )
        menu = {e.name: e for e in catalog.snapshot().commands["router"]}
        assert menu["summarize-then-rank"].description == "comparing many courses"

        runs = []
        for edit in (None, "Rank the courses by workload, then summarize."):
            if edit:
                lib.put_decomposition(text(example("summarize then rank", edit)))
            run_dir = tmp_path / f"run{len(runs)}"
            source = catalog.materialize("router", run_dir=run_dir)
            fake.requests.clear()
            done = run_dr(
                source.config_path, "Which course comes after CS101?", cwd=tmp_path
            )
            assert (done.returncode, done.stdout.splitlines()[-1]) == (0, "done")
            runs.append((source, first_user_messages(fake.requests[0])))

    (first, first_asks), (second, second_asks) = runs
    assert (first.namespace, second.namespace) == ("router", "router")
    assert first.versions["decompositions"]["summarize then rank"] == 1
    assert second.versions["decompositions"]["summarize then rank"] == 2
    assert "Summarize each course, then rank them." in first_asks
    assert "Rank the courses by workload, then summarize." in second_asks
    assert "Summarize each course, then rank them." not in second_asks
    assert dataclasses.asdict(first)["client"]["base_url"].startswith(
        "http://127.0.0.1:"
    )
