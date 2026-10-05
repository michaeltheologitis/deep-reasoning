import hashlib
import os
from pathlib import Path

import pytest
import yaml

from deep_reasoning.acp.catalog import CommandEntry, ConfigCatalog, RunSource, slug


def decomposition(name: str) -> dict:
    return {
        "name": name,
        "messages": [
            {"role": "user", "content": "{{ task }}"},
            {"role": "assistant", "content": "<repl>\nFinalAnswer(task)\n</repl>"},
        ],
    }


def entry(name: str, decomposition: str) -> CommandEntry:
    return CommandEntry(
        name,
        decomposition,
        f"Open with the '{decomposition}' decomposition",
        "the task",
    )


@pytest.fixture
def config(tmp_path: Path) -> Path:
    (tmp_path / "cfg" / "ns").mkdir(parents=True)
    (tmp_path / "cfg" / "ns" / "extra.yaml").write_text(
        yaml.safe_dump({"decompositions": [decomposition("deep dive")]})
    )
    path = tmp_path / "cfg" / "main.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "system_prompt": "s",
                "model": "m",
                "client": {"base_url": "http://127.0.0.1:9/v1", "api_key_env": "K"},
                "entry_namespace": "router",
                "namespaces_dir": "ns",
                "decompositions": [decomposition("triage"), decomposition("Triage!")],
                "namespaces": {
                    "router": {
                        "decompositions": [
                            decomposition("summarize then rank"),
                            decomposition("triage"),
                        ]
                    },
                    "advising": {
                        "decompositions": [decomposition("compare departments")]
                    },
                },
            }
        )
    )
    return path


def test_every_namespace_offers_the_configs_decompositions_ahead_of_its_own(
    config, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    snapshot = ConfigCatalog(config).snapshot()
    assert snapshot.namespaces == ("root", "advising", "extra", "router")
    assert snapshot.default_namespace == "router"
    top = (entry("triage", "triage"), entry("triage-2", "Triage!"))
    assert snapshot.commands == {
        "root": top,
        "advising": (*top, entry("compare-departments", "compare departments")),
        "extra": (*top, entry("deep-dive", "deep dive")),
        "router": (*top, entry("summarize-then-rank", "summarize then rank")),
    }


def test_materialize_hands_the_worker_the_config_as_it_is(config, tmp_path):
    source = ConfigCatalog(config).materialize("advising", run_dir=tmp_path / "run")
    assert source == RunSource(
        config_path=config,
        namespace="advising",
        client=source.client,
        versions={"config_sha256": hashlib.sha256(config.read_bytes()).hexdigest()},
    )
    assert source.client["base_url"] == "http://127.0.0.1:9/v1"
    assert source.tool_clients == {}


def test_materialize_hands_the_worker_each_tools_own_client(tmp_path):
    rag_client = {"base_url": "http://127.0.0.1:9/v1", "api_key_env": "EMBED_KEY"}
    path = tmp_path / "main.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "system_prompt": "s",
                "model": "m",
                "tools": {
                    "rag": {"embed_model": "e", "client": rag_client},
                    "kg": {"persist": "kg"},
                },
            }
        )
    )
    source = ConfigCatalog(path).materialize("root", run_dir=tmp_path / "run")
    assert source.tool_clients == {"rag": rag_client}


@pytest.mark.parametrize(
    ("name", "slugged"),
    [
        ("summarize then rank", "summarize-then-rank"),
        ("  Compare: Departments! ", "compare-departments"),
        ("a__b", "a-b"),
    ],
)
def test_a_command_is_its_decomposition_name_slugged(name, slugged):
    assert slug(name) == slugged


BETA = os.environ.get("DR_BETA_CHECKOUT")


def beta_configs() -> list[Path]:
    """The run configs among deep_reasoner_beta's docs/configs: the files that name a model
    or a system prompt (the rest are fragments they compose, or data)."""
    if not BETA:
        return []
    found = []
    for path in sorted(Path(BETA, "docs", "configs").rglob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if (
            "namespaces" not in path.parent.parts
            and isinstance(data, dict)
            and {"model", "system_prompt"} & set(data)
        ):
            found.append(path)
    return found


@pytest.mark.skipif(
    not BETA, reason="DR_BETA_CHECKOUT names no deep_reasoner_beta checkout"
)
@pytest.mark.parametrize(
    "main", beta_configs(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_deep_reasoner_betas_own_configs_read_into_a_catalog(main):
    snapshot = ConfigCatalog(main).snapshot()
    assert snapshot.namespaces[0] == "root"
    assert snapshot.default_namespace in snapshot.namespaces
    assert set(snapshot.commands) == set(snapshot.namespaces)
