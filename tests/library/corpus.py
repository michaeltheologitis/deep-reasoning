"""deep_reasoner_beta's own configs, read in place from the checkout DR_BETA_CHECKOUT names
(never copied into this repo: it has no license)."""

import os
from pathlib import Path

BETA = (
    Path(os.environ["DR_BETA_CHECKOUT"]) if os.environ.get("DR_BETA_CHECKOUT") else None
)
SKIP_REASON = "DR_BETA_CHECKOUT names no deep_reasoner_beta checkout"
FOLDERS = ("docs/configs", "configs")

# Namespace files whose `tools:` is a list: V2Config refuses them, by design. Their
# directories are covered by namespaces_dir.yaml and by NAMESPACES_DIR_CONFIG.
NOT_CONFIGS = frozenset(
    {
        "configs/example/namespaces/root.yaml",
        "docs/configs/catalog/namespaces/root.yaml",
    }
)


def corpus() -> list[str]:
    """Every *.yaml under the two folders, relative to the checkout."""
    if BETA is None:
        return []
    found = (p for folder in FOLDERS for p in (BETA / folder).rglob("*.yaml"))
    return sorted(str(p.relative_to(BETA)) for p in found)


def configs() -> list[str]:
    return [name for name in corpus() if name not in NOT_CONFIGS]


def namespaces_dir_config(directory: Path) -> Path:
    """The example's main.yaml composed with its namespaces directory, which no corpus
    file loads."""
    path = directory / "example_with_namespaces.yaml"
    path.write_text(
        f"_compose:\n  - {BETA / 'configs/example/main.yaml'}\n"
        f"namespaces_dir: {BETA / 'configs/example/namespaces'}\n"
    )
    return path
