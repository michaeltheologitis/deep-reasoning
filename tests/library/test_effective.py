import pytest
from deep_reasoner.repls import ReplConfig
from pydantic import TypeAdapter

from deep_reasoning.library import Library
from deep_reasoning.library.effective import chain, resolved
from tests.library import corpus
from tests.library.conftest import example, text


@pytest.fixture
def layered(lib):
    lib.put_profile("model: m\nrepl: {type: local}\n")
    lib.put_tool("search", "factory: llm\n")
    for name in ("a", "b"):
        lib.put_decomposition(text(example(name)))
    lib.put_namespace(
        "name: root\ntools: [llm]\nvars: {x: 1, y: 1}\nsystem_suffix: Be brief.\n",
        decompositions=["a"],
    )
    lib.put_namespace(
        "name: math\nspawn: [math.geometry]\nreasoner: {type: chat}\ntools: [search, llm]\n"
        "vars: {y: 2}\nsystem_suffix: Show the arithmetic.\n",
        decompositions=["a", "b"],
    )
    lib.put_namespace("name: math.geometry\ntools: [ruler]\nvars: {z: 3}\n")
    return lib


@pytest.mark.parametrize(
    ("field", "namespace", "expected"),
    [
        ("chain", "math.geometry", ["root", "math", "math.geometry"]),
        ("repl", "math.geometry", {"value": {"type": "local"}, "source": "profile"}),
        ("reasoner", "math.geometry", {"value": {"type": "chat"}, "source": "math"}),
        ("reasoner", "root", {"value": None, "source": None}),
        ("spawn", "math.geometry", {"value": ["math.geometry"], "source": "math"}),
        (
            "system_suffix",
            "math.geometry",
            [
                {"source": "root", "text": "Be brief."},
                {"source": "math", "text": "Show the arithmetic."},
            ],
        ),
        (
            "tools",
            "math.geometry",
            [
                {"name": "llm", "source": "root", "defined": True},
                {"name": "search", "source": "math", "defined": True},
                {"name": "ruler", "source": "math.geometry", "defined": False},
            ],
        ),
        (
            "vars",
            "math.geometry",
            {
                "x": {"value": 1, "source": "root"},
                "y": {"value": 2, "source": "math"},
                "z": {"value": 3, "source": "math.geometry"},
            },
        ),
        (
            "decompositions",
            "math",
            [
                {
                    "name": "a",
                    "slug": "a",
                    "version": 1,
                    "use_when": None,
                    "source": "math",
                },
                {
                    "name": "b",
                    "slug": "b",
                    "version": 1,
                    "use_when": None,
                    "source": "math",
                },
            ],
        ),
    ],
)
def test_each_inherited_value_names_the_level_it_comes_from(
    layered, field, namespace, expected
):
    assert layered.effective(namespace).model_dump(mode="json")[field] == expected


def test_a_repl_set_in_a_namespace_is_its_source(layered):
    layered.put_namespace("name: math.geometry\nrepl: {type: restricted}\n")
    repl = layered.effective("math.geometry").repl
    assert (repl.source, repl.value["type"]) == ("math.geometry", "restricted")


def assert_sources_rebuild_resolve(lib: Library, namespace: str) -> None:
    """Every value read back from the level its source names equals deep_reasoner's
    resolve, and no later level sets it."""
    state = lib.state()
    values = resolved(state, namespace)
    view = lib.effective(namespace)
    data = {name: state.namespaces[name].data for name in chain(namespace)}
    later = {name: chain(namespace)[i + 1 :] for i, name in enumerate(chain(namespace))}
    profile_repl = state.profile.data.get("repl", {"type": "local"})
    repl = (
        data[view.repl.source]["repl"]
        if view.repl.source != "profile"
        else profile_repl
    )
    assert TypeAdapter(ReplConfig).validate_python(repl) == values.repl
    for key in ("reasoner", "spawn"):
        source = getattr(view, key).source
        assert (data[source][key] if source else None) == getattr(values, key)
        assert source is None or all(data[n].get(key) is None for n in later[source])
    joined = "\n\n".join(part.text for part in view.system_suffix) or None
    assert joined == values.system_suffix
    assert [t.name for t in view.tools] == values.tools
    for tool in view.tools:
        assert tool.name in data[tool.source].get("tools", [])
    for key, sourced in view.vars.items():
        assert data[sourced.source]["vars"][key] == values.vars[key] == sourced.value
        assert all(key not in data[n].get("vars", {}) for n in later[sourced.source])
    by_name = {d.name: d for d in values.decompositions}
    assert [d.name for d in view.decompositions] == list(by_name)
    for d in view.decompositions:
        assert d.name in state.namespaces[d.source].decompositions
        assert state.decompositions[d.name].data == by_name[d.name].model_dump(
            mode="json"
        )


def test_the_sources_rebuild_deep_reasoners_resolve(layered):
    for namespace in ("root", "math", "math.geometry"):
        assert_sources_rebuild_resolve(layered, namespace)


@pytest.mark.skipif(corpus.BETA is None, reason=corpus.SKIP_REASON)
@pytest.mark.parametrize("name", corpus.configs())
def test_effective_values_equal_deep_reasoners_resolve(name, tmp_path):
    lib = Library.open(tmp_path / "library.sqlite", starter=False)
    lib.import_config(corpus.BETA / name)
    for ns in lib.namespaces():
        assert_sources_rebuild_resolve(lib, ns.name)
