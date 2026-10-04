"""dr-acp's command line, and the stdio integrity it guards (E2)."""

import sys
from pathlib import Path

from deep_reasoning.acp import proxy
from deep_reasoning.acp.cli import Options, parse_options
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from tests.acp.harness import dr_acp, run
from tests.acp.scenarios import BY_NAME, repl, scripted

TEN_MB = 10 * 1024 * 1024
PLAN = {
    "Be noisy.": [
        repl(
            "import os, sys",
            f"sys.stdout.write('x' * {TEN_MB})",
            "os.write(1, b'raw bytes on fd 1\\n')",
            "print('quiet')",
        ),
        repl(f"print('y' * {TEN_MB})"),
        repl("FinalAnswer('survived')"),
    ],
}
# Runs dr-acp with an import hook that prints, to stdout and to fd 1, while the front
# imports its own modules after start-up.
NOISY_FRONT = """
import importlib.abc, os, sys

class Noisy(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name == "deep_reasoning.acp.agent":
            print("noise from an import")
            os.write(1, b"raw noise from an import\\n")
        return None

sys.meta_path.insert(0, Noisy())
from deep_reasoning.acp.cli import main
sys.exit(main(sys.argv[1:]))
"""


def test_writes_to_stdout_inside_a_run_never_reach_the_acp_stream(tmp_path, home, work):
    async def body():
        async with FakeOpenAI(scripted(PLAN)) as model:
            config = BY_NAME["linear"].write_config(tmp_path / "config", model.base_url)
            async with dr_acp(config, home) as client:
                root = await client.open_session(work)
                response = await client.ask(root, "Be noisy.")
                return response, client.updates_on(root)

    response, updates = run(body())
    assert response.field_meta["deep_reasoner"]["outcome"] == "answered"
    outputs = [
        u["rawOutput"] for u in updates if u["sessionUpdate"] == "tool_call_update"
    ]
    assert outputs[0] == "quiet"
    assert len(outputs[1].encode()) < TEN_MB
    assert "bytes elided" in outputs[1]


def test_a_print_while_the_front_imports_cannot_corrupt_the_stream(
    tmp_path, home, work
):
    config = BY_NAME["linear"].write_config(
        tmp_path / "config", "http://127.0.0.1:9/v1"
    )

    async def body():
        command = (sys.executable, "-c", NOISY_FRONT)
        async with dr_acp(config, home, command=command) as client:
            await client.open_session(work)
        return client

    client = run(body())
    assert "noise from an import" in client.stderr_text()


def test_without_a_config_dr_acp_serves_the_library_at_its_home(tmp_path, home, work):
    async def body():
        async with dr_acp(None, home) as client:
            root = await client.open_session(work)
            return client.printer.commands[root]

    assert run(body()) == []
    assert (home / "library.sqlite").is_file()


def test_options_default_to_native_a_minute_of_heartbeat_warnings_and_the_proxy():
    assert parse_options(["--config", "main.yaml"]) == Options(
        config=Path("main.yaml"),
        home=None,
        flat=False,
        heartbeat_s=60.0,
        log_level="WARNING",
        key_proxy=True,
        spend_cap_usd=proxy.DEFAULT_SPEND_CAP_USD,
    )
    assert parse_options(
        [
            "--config",
            "c.yaml",
            "--home",
            "h",
            "--flat",
            "--heartbeat",
            "5",
            "--log-level",
            "DEBUG",
            "--no-key-proxy",
            "--spend-cap-usd",
            "0.5",
        ]
    ) == Options(
        config=Path("c.yaml"),
        home=Path("h"),
        flat=True,
        heartbeat_s=5.0,
        log_level="DEBUG",
        key_proxy=False,
        spend_cap_usd=0.5,
    )
