"""Every sentence dr-web prints, verbatim from TASK-48 §5.1.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

NO_UV = (
    "✗ uv was not found: run this command with uvx, which comes with uv "
    "(https://docs.astral.sh/uv/)."
)


def installing_node(version: str) -> str:
    return f"Installing Node {version} for Deep Reasoning, once (about 55 MB) …"


def node_failed(step: str, code: str) -> str:
    return (
        f"✗ Installing Node failed ({step} exited {code}); its output is above. Check "
        "that this computer is online, then run the same command again."
    )


def fetching(version: str) -> str:
    return f"Fetching Deep Reasoning {version} for your browser, once (about 3 MB) …"


def fetch_failed(name: str, where: str, reason: str) -> str:
    return (
        f"✗ Could not download {name} from {where} ({reason}): check that this "
        "computer is online, then run the same command again. Nothing was changed."
    )


def not_a_tarball(path: str, reason: str) -> str:
    return (
        f"✗ {path} is not a Deep Reasoning browser tarball ({reason}). Nothing was "
        "changed."
    )


def unpack_failed(path: str, where: str, why: str) -> str:
    return f"✗ Could not unpack {path} into {where} ({why}). Nothing was changed."
