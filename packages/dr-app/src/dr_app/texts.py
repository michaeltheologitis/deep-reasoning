"""Every sentence dr-app prints, verbatim from D5 §6.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

NO_GIT = (
    "✗ deep_reasoner is fetched with git, which was not found. On macOS run "
    "xcode-select --install; on Linux install git."
)
NO_UV = (
    "✗ uv was not found on PATH. The app bundles it: reinstall the app. In a terminal, "
    "install uv from https://docs.astral.sh/uv/."
)
NOTHING_INSTALLED = (
    "✗ Nothing is installed yet: launch the app once, then run this again."
)


def no_access_dr(host_path: str) -> str:
    return (
        f"✗ Could not read {host_path} with your git credentials. It is private: ask Dean "
        "for read access, then sign git in for https (gh auth login, or an SSH key and "
        'git config --global url."git@github.com:".insteadOf "https://github.com/") and '
        "restart. Nothing was installed."
    )


def checks_ok(version: str, host_path: str) -> str:
    return f"git {version} ✓ · {host_path} readable ✓"


def safety(cap: str) -> str:
    return (
        "deep_reasoner runs as you. It can read and change any file you can, and code it "
        "writes can find your model keys on this computer if it tries. Spend through the "
        f"key proxy stops at ${cap} per conversation."
    )


def installing(commit7: str, dr_commit7: str) -> str:
    return (
        f"installing deep-reasoning {commit7} with deep_reasoner {dr_commit7} … "
        "(first launch, or after an update: a few minutes)"
    )


def installed(duration: str) -> str:
    return f"installed in {duration}"


def install_failed(commit7: str, step: str, code: str) -> str:
    return (
        f"✗ Installing deep-reasoning {commit7} failed ({step} exited {code}); its "
        "output is above. After an update this needs the network once: connect and "
        "restart."
    )


def home_local(home: str) -> str:
    return f"your data: {home}"


def home_network(fstype: str, home: str) -> str:
    return (
        f"Your home directory is on a network filesystem ({fstype}), where the Library's "
        f"database is unsafe, so your data is kept on this computer at {home}. The system "
        "may delete files there that go unused for 30 days: export your Library now and "
        "then (dr-app export DIR), or choose another folder with dr-app home DIR."
    )


def home_unsafe(path: str, owner: str, mode: str) -> str:
    return (
        f"✗ {path} exists but is not a private folder of yours (owner {owner}, mode "
        f"{mode}). Remove it, or choose another folder with dr-app home DIR."
    )


def home_too_long(home: str, length: str, limit: str) -> str:
    return (
        f"✗ {home} is too long a path for your data: deep_reasoner's Claude runs serve "
        f"sockets under it up to {length} bytes long, and this system allows {limit}. "
        "Choose a shorter folder with dr-app home DIR."
    )


def home_set(home: str, old: str) -> str:
    return (
        f"Your data will be kept in {home} from the next launch. Nothing was moved: copy "
        f"library.sqlite, runs/, sessions/ and spend/ from {old} yourself, or export the "
        "Library and import it there."
    )


def home_refused(path: str, reason: str) -> str:
    """reason: 'is not an absolute path' or 'is on a network filesystem (nfs4)'."""
    return (
        f"✗ {path} {reason}: choose an absolute path to a folder on this computer with "
        "dr-app home DIR."
    )


def state_from_a_newer_app(path: str, version: str) -> str:
    return (
        f"✗ {path} was written by a newer Deep Reasoning (its version {version}; this one "
        "reads 1). Install the newer app again. To set this one up from the start "
        f"instead, delete {path}: your data stays, but a folder chosen with dr-app home "
        "is forgotten."
    )


def state_unusable(path: str, reason: str) -> str:
    return (
        f"✗ {path} cannot be used: {reason}. Delete it and launch the app again: setup "
        "then installs as on a first launch, which needs the network. Your data stays, "
        "but a folder chosen with dr-app home must be chosen again."
    )
