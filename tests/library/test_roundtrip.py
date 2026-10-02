"""E7 · Round-trip (design §7.1): every config in deep_reasoner_beta's docs/configs and
configs imported, materialized, loaded and resolved to equal namespaces, and given the
same scripted answer by dr on the original and on its copy."""

import os
import shutil
from pathlib import Path
from typing import Any

import pytest
from deep_reasoner.mocks import write_fake_claude_cli
from deep_reasoner.namespaces import ROOT, load_namespaces_from_dir
from deep_reasoner.v2.cli import build_namespace_registry

from deep_reasoning.acp.catalog import load_dr_config
from deep_reasoning.library import Library, LibraryImportError
from tests.library import corpus
from tests.library.conftest import run_dr
from tests.library.fake_openai import FakeOpenAI

TASK = "Which course comes after CS101?"
ANSWER = '<think>ok</think>\n<repl>\nFinalAnswer("done")\n</repl>'
# Model providers' keys get a dummy; DAYTONA_API_KEY stays unset, so a Daytona REPL
# fails before it reaches the network.
DUMMY_KEYS = ("OPENROUTER_API_KEY", "NOVITA_API_KEY", "OPENAI_API_KEY", "FAKE_KEY")
# Nothing but the fake is reachable: any other host goes to a closed port.
OFFLINE = {
    "HTTPS_PROXY": "http://127.0.0.1:9",
    "HTTP_PROXY": "http://127.0.0.1:9",
    "https_proxy": "http://127.0.0.1:9",
    "http_proxy": "http://127.0.0.1:9",
    "NO_PROXY": "127.0.0.1,localhost",
    "no_proxy": "127.0.0.1,localhost",
}
# The configs that reached the fake's answer on both sides at d7334ae, and the two whose
# backbone is a Claude session (the fake CLI's, which never calls FinalAnswer): a broken
# fake or harness cannot make every case "equal" by failing everywhere.
ANSWERING = frozenset(
    {
        "configs/example/main.yaml",
        "configs/example/rag.yaml",
        "configs/example/safe_url.yaml",
        "configs/example/v2_namespaces.yaml",
        "docs/configs/catalog/advisors.yaml",
        "docs/configs/catalog/crossover.yaml",
        "docs/configs/catalog/kg_agent.yaml",
        "docs/configs/catalog/kg_query.yaml",
        "docs/configs/catalog/llm.yaml",
        "docs/configs/catalog/llm_tool.yaml",
        "docs/configs/catalog/main.yaml",
        "docs/configs/catalog/namespaces.yaml",
        "docs/configs/catalog/namespaces_dir.yaml",
        "docs/configs/catalog/restricted.yaml",
        "docs/configs/catalog/sandboxes.yaml",
        "docs/configs/examples/cruncher/cruncher.yaml",
        "docs/configs/examples/experience/experience.yaml",
        "docs/configs/examples/research/assistant.yaml",
        "docs/configs/examples/waitlist/waitlist.yaml",
    }
)
CLAUDE_BACKBONE = frozenset(
    {"docs/configs/catalog/claude.yaml", "docs/configs/incidents/triage.yaml"}
)
CLAUDE_ENDED = "The Claude session ended without calling FinalAnswer"
EXAMPLE_WITH_NAMESPACES = "configs/example (main.yaml + namespaces/)"

needs_beta = pytest.mark.skipif(corpus.BETA is None, reason=corpus.SKIP_REASON)


def comparable(cfg: Any) -> dict[str, Any]:
    """The config without what materialize moves: its path, its namespaces, and each tool
    file's location."""
    data = cfg.model_dump(
        mode="json", exclude={"config_path", "namespaces", "namespaces_dir"}
    )
    data["tools"] = {
        name: {k: v for k, v in block.items() if k != "factory_from"}
        for name, block in data["tools"].items()
    }
    return data


def namespace_names(cfg: Any) -> set[str]:
    found = (
        {ns.name for ns in load_namespaces_from_dir(cfg.namespaces_dir)}
        if cfg.namespaces_dir
        else set()
    )
    return {ROOT, *found, *cfg.namespaces}


def resolutions(cfg: Any, names: set[str]) -> dict[str, Any]:
    """deep_reasoner's resolve for every namespace, or the error it raises."""
    registry = build_namespace_registry(cfg)
    try:
        found = {}
        for name in sorted(names):
            try:
                found[name] = registry.resolve(name)
            except ValueError as exc:
                found[name] = f"ValueError: {exc}"
        return found
    finally:
        registry.close()


def rows(lib: Library) -> dict[str, Any]:
    state = lib.state()
    return {
        "profile": (state.profile.yaml, state.profile.decompositions),
        "namespaces": {
            n: (r.yaml, r.decompositions) for n, r in state.namespaces.items()
        },
        "decompositions": {
            n: (r.yaml, r.slug, r.use_when, r.hint)
            for n, r in state.decompositions.items()
        },
        "tools": {n: (r.yaml, r.source) for n, r in state.tools.items()},
    }


def round_trip(path: Path, tmp_path: Path) -> Path:
    """Level 1; returns the materialized main.yaml."""
    original = load_dr_config(path)
    lib = Library.open(tmp_path / "first.sqlite", starter=False)
    lib.import_config(path)
    out = lib.materialize(tmp_path / "materialized", namespace=original.entry_namespace)
    copy = load_dr_config(out / "main.yaml")

    assert comparable(copy) == comparable(original)

    names = namespace_names(original)
    assert namespace_names(copy) == names
    assert resolutions(copy, names) == resolutions(load_dr_config(path), names)

    for name, block in original.tools.items():
        if "factory_from" in block:
            source = Path(original.config_path).parent / block["factory_from"]
            assert (out / "tools" / f"{name}.py").read_bytes() == source.read_bytes()

    second = Library.open(tmp_path / "second.sqlite", starter=False)
    second.import_config(out)
    assert rows(second) == rows(lib)
    assert lib.import_config(out).rev is None
    return out / "main.yaml"


@needs_beta
@pytest.mark.parametrize("name", corpus.corpus())
def test_every_config_dr_accepts_round_trips(name, tmp_path):
    path = corpus.BETA / name
    if name in corpus.NOT_CONFIGS:
        with pytest.raises(
            LibraryImportError, match="tools\n  Input should be a valid dictionary"
        ):
            Library.open(tmp_path / "first.sqlite", starter=False).import_config(path)
        return
    round_trip(path, tmp_path)


@needs_beta
def test_the_example_namespaces_directory_round_trips(tmp_path):
    round_trip(corpus.namespaces_dir_config(tmp_path), tmp_path)


def test_the_corpus_is_read_in_ci():
    assert os.environ.get("CI") != "true" or corpus.BETA is not None


def working_folder(name: str, root: Path) -> Path:
    """A folder holding a copy of the corpus folder the config is under, as `configs`, so
    data paths such as configs/example/docs.yaml resolve, and whatever a tool writes
    beside its data (rag's embeddings sidecar) lands here, never in the checkout."""
    folder = next(f for f in corpus.FOLDERS if name.startswith(f"{f}/"))
    root.mkdir()
    shutil.copytree(corpus.BETA / folder, root / "configs")
    return root


def scripted_run(
    config: Path, cwd: Path, fake: FakeOpenAI, bin_dir: Path
) -> tuple[int, str, Any]:
    """dr on config against the fake: (exit code, last line of stdout, first request's
    messages)."""
    cfg = load_dr_config(config)
    sets = [f"client.base_url={fake.base_url}"] + [
        f"tools.{name}.client.base_url={fake.base_url}"
        for name, block in cfg.tools.items()
        if "client" in block
    ]
    env = {
        **OFFLINE,
        # The original's factory_from file is imported in place: no __pycache__ beside it.
        "PYTHONDONTWRITEBYTECODE": "1",
        **{key: "dummy" for key in DUMMY_KEYS},
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
    }
    fake.requests.clear()
    done = run_dr(config, TASK, cwd=cwd, sets=sets, env=env)
    lines = done.stdout.strip().splitlines()
    first = fake.requests[0]["messages"] if fake.requests else None
    return done.returncode, lines[-1] if lines else "", first


@pytest.fixture(scope="module")
def fake():
    with FakeOpenAI(ANSWER) as running:
        yield running


@pytest.fixture(scope="module")
def bin_dir(tmp_path_factory) -> Path:
    """deep_reasoner's fake Claude CLI, first on PATH as `claude`."""
    directory = tmp_path_factory.mktemp("bin")
    (directory / "claude").symlink_to(write_fake_claude_cli(directory))
    assert shutil.which("claude", path=str(directory)) == str(directory / "claude")
    return directory


@needs_beta
@pytest.mark.parametrize("name", [*corpus.configs(), EXAMPLE_WITH_NAMESPACES])
def test_dr_answers_the_same_from_the_original_and_its_copy(
    name, tmp_path, fake, bin_dir
):
    if name == EXAMPLE_WITH_NAMESPACES:
        original, folder = corpus.namespaces_dir_config(tmp_path), "configs/x"
    else:
        original, folder = corpus.BETA / name, name
    copy = round_trip(original, tmp_path)
    before = scripted_run(
        original, working_folder(folder, tmp_path / "a"), fake, bin_dir
    )
    after = scripted_run(copy, working_folder(folder, tmp_path / "b"), fake, bin_dir)
    assert after == before
    if name in ANSWERING:
        assert before[:2] == (0, "done")
    if name in CLAUDE_BACKBONE:
        assert before[0] == 0 and before[1].startswith(CLAUDE_ENDED)
