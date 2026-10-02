from pathlib import Path

import pytest
import yaml
from deep_reasoner.v2.cli import build_namespace_registry

from deep_reasoning.acp.catalog import load_dr_config
from deep_reasoning.library import LibraryNotFound, LibraryRefused, Manifest, shapes
from tests.library.conftest import example, text


def files(directory) -> list[str]:
    return sorted(
        str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()
    )


@pytest.fixture
def imported(lib, router):
    lib.import_config(router)
    lib.put_tool(
        "waitlist",
        "factory: make\n",
        source="def make(c, p): ...\n",
        granted_in=["courses"],
    )
    return lib


def test_materialized_directory_layout(imported, tmp_path):
    out = imported.materialize(tmp_path / "out")
    assert out == tmp_path / "out"
    assert files(out) == [
        "library.yaml",
        "main.yaml",
        "namespaces/courses.yaml",
        "namespaces/root.yaml",
        "namespaces/router.yaml",
        "tools/waitlist.py",
    ]
    main = (out / "main.yaml").read_text()
    assert main.startswith(
        f"# Written by the deep-reasoning Library from {imported.path} at revision 3. "
        "Edit the Library, not this file.\n"
    )
    data = yaml.safe_load(main)
    assert data["entry_namespace"] == "router"
    assert data["namespaces_dir"] == "namespaces"
    assert data["tools"] == {
        "waitlist": {"factory": "make", "factory_from": "tools/waitlist.py"}
    }
    assert (out / "tools" / "waitlist.py").read_text() == "def make(c, p): ...\n"


def test_the_materialized_config_loads_and_resolves_like_the_library(
    imported, tmp_path
):
    cfg = load_dr_config(imported.materialize(tmp_path / "out") / "main.yaml")
    registry = build_namespace_registry(cfg)
    try:
        assert sorted(registry._by_name) == ["courses", "root", "router"]
        courses = registry.resolve("courses")
        assert courses.tools == ["llm", "waitlist"]
        assert [d.name for d in courses.decompositions] == ["catalog lookup"]
        assert courses.vars["catalog"]["CS201"]["prereqs"] == ["CS101"]
    finally:
        registry.close()
    assert cfg.model == "m-small" and cfg.max_iter == 5


def test_decompositions_are_inlined_in_attachment_order(imported, tmp_path):
    imported.put_namespace(
        "name: router", decompositions=["decline", "route a course question"]
    )
    out = imported.materialize(tmp_path / "out")
    router = yaml.safe_load((out / "namespaces" / "router.yaml").read_text())
    assert [d["name"] for d in router["decompositions"]] == [
        "decline",
        "route a course question",
    ]
    assert router["decompositions"][0] == example("decline")


def test_top_level_decompositions_are_written_into_main(imported, tmp_path):
    imported.put_decomposition(text(example("triage")), top_level=True)
    out = imported.materialize(tmp_path / "out")
    assert yaml.safe_load((out / "main.yaml").read_text())["decompositions"] == [
        example("triage")
    ]


def test_materialize_as_of_an_old_revision(imported, tmp_path):
    imported.put_decomposition(text(example("catalog lookup", "Edited?")))
    old = imported.materialize(tmp_path / "old", rev=2)
    new = imported.materialize(tmp_path / "new")
    contents = [
        yaml.safe_load((d / "namespaces" / "courses.yaml").read_text())[
            "decompositions"
        ][0]
        for d in (old, new)
    ]
    assert [c["messages"][0]["content"] for c in contents] == [
        "Which course comes after CS101?",
        "Edited?",
    ]
    assert not (old / "tools").exists()


def test_the_manifest_records_every_version(imported, tmp_path):
    imported.put_decomposition(
        text(example("decline")), use_when="off-topic", hint="it"
    )
    out = imported.materialize(tmp_path / "out", namespace="courses")
    manifest = Manifest.model_validate(
        yaml.safe_load((out / "library.yaml").read_text())
    )
    assert manifest.versions() == {
        "v": 1,
        "library": str(imported.path),
        "rev": 4,
        "namespace": "courses",
        "deep_reasoner": shapes.deep_reasoner_build(),
        "profile": 2,
        "namespaces": {"root": 2, "router": 1, "courses": 2},
        "decompositions": {
            "route a course question": 1,
            "decline": 2,
            "catalog lookup": 1,
        },
        "tools": {"waitlist": 1},
    }
    assert manifest.metadata["decline"].model_dump() == {
        "use_when": "off-topic",
        "hint": "it",
    }
    assert (
        yaml.safe_load((out / "main.yaml").read_text())["entry_namespace"] == "courses"
    )


def test_a_namespace_that_is_not_live_is_not_found(imported, tmp_path):
    with pytest.raises(LibraryNotFound, match="There is no namespace 'gone'"):
        imported.materialize(tmp_path / "out", namespace="gone")


def test_a_non_empty_destination_is_refused(imported, tmp_path):
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "keep.txt").write_text("mine")
    with pytest.raises(LibraryRefused, match="is not empty"):
        imported.materialize(tmp_path / "out")
    assert files(tmp_path / "out") == ["keep.txt"]
    (tmp_path / "empty").mkdir()
    assert (imported.materialize(tmp_path / "empty") / "main.yaml").is_file()


def test_a_failed_write_leaves_no_directory(imported, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("disk full")

    # The namespace files are written before the tool files.
    monkeypatch.setattr(Path, "write_bytes", fail)
    with pytest.raises(OSError, match="disk full"):
        imported.materialize(tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_without_a_destination_it_writes_a_new_temporary_directory(imported):
    first, second = imported.materialize(), imported.materialize()
    assert first != second
    assert (first / "main.yaml").read_text() == (second / "main.yaml").read_text()
