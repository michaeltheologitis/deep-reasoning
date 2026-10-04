import pytest
import yaml

from deep_reasoning.acp.worker.protocol import Start
from deep_reasoning.acp.worker.runner import as_text, run_config


@pytest.mark.parametrize(
    ("value", "text"),
    [("CS is heavy", "CS is heavy"), (42, "42"), (["a"], "['a']"), (None, "None")],
)
def test_an_answer_is_its_text_or_its_repr(value, text):
    assert as_text(value) == text


def test_the_run_config_takes_the_namespace_and_every_clients_overrides(tmp_path):
    path = tmp_path / "main.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "system_prompt": "s",
                "model": "m",
                "client": {
                    "base_url": "https://up",
                    "api_key_env": "K",
                    "max_retries": 0,
                },
                "tools": {
                    "rag": {
                        "embed_model": "e",
                        "client": {"base_url": "https://embed", "api_key_env": "K"},
                    },
                    "kg": {"persist": "kg"},
                },
            }
        )
    )
    start = Start(
        run="r",
        session="s",
        run_dir=str(tmp_path / "run"),
        config_path=str(path),
        namespace="advising",
        client_overrides={"base_url": "http://127.0.0.1:1/r/a", "api_key_env": "T"},
        tool_client_overrides={"rag": {"base_url": "http://127.0.0.1:1/r/b"}},
    )
    cfg = run_config(start)
    assert cfg.entry_namespace == "advising"
    assert (cfg.client.base_url, cfg.client.api_key_env, cfg.client.max_retries) == (
        "http://127.0.0.1:1/r/a",
        "T",
        0,
    )
    assert cfg.tools["rag"]["client"] == {
        "base_url": "http://127.0.0.1:1/r/b",
        "api_key_env": "K",
    }
    assert "client" not in cfg.tools["kg"]


def test_a_start_without_tool_overrides_leaves_every_tool_as_configured():
    start = Start.model_validate_json(
        '{"run": "r", "session": "s", "run_dir": "d", "config_path": "c",'
        ' "namespace": "root", "client_overrides": {}}'
    )
    assert start.tool_client_overrides == {}
