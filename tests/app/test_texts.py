from dr_app import texts


def test_sentences_without_fields_are_the_designs_verbatim():
    assert texts.NO_GIT == (
        "✗ Deep Reasoning is installed with git, which was not found. On macOS run "
        "xcode-select --install; on Linux install git."
    )
    assert texts.PROFILE_CREATED == (
        "Deep Reasoning's agent profile created and made the default"
    )
    assert texts.PROFILE_UPDATED == "Deep Reasoning's agent profile updated"
    assert texts.APP_DISABLED == (
        "App dr-library is disabled, so Show Decompositions is hidden. Enable it under "
        "Apps to use it."
    )


def test_sentences_with_fields_are_the_designs_verbatim():
    assert texts.no_access_dr("github.com/DeanLight/deep_reasoner_beta") == (
        "✗ Could not read github.com/DeanLight/deep_reasoner_beta with your git "
        "credentials. It is private: ask Dean for read access, then sign git in for https "
        '(gh auth login, or an SSH key and git config --global url."git@github.com:"'
        '.insteadOf "https://github.com/") and restart. Nothing was installed.'
    )
    assert (
        texts.checks_ok("2.39.5", "github.com/a/b")
        == "git 2.39.5 ✓ · github.com/a/b readable ✓"
    )
    assert texts.installing("a1b2c3d", "d7334ae") == (
        "installing Deep Reasoning a1b2c3d with deep_reasoner d7334ae … (first launch, "
        "or after an update: a few minutes)"
    )
    assert texts.install_failed("a1b2c3d", "uv sync", "2") == (
        "✗ Installing Deep Reasoning a1b2c3d failed (uv sync exited 2); its output is "
        "above. After an update this needs the network once: connect and restart."
    )
    assert texts.home_too_long("/home/m/data", "112", "108") == (
        "✗ /home/m/data is too long a path for your data: Deep Reasoning's Claude runs "
        "serve sockets under it up to 112 bytes long, and this system allows 108. "
        "Choose a shorter folder with dr-app home DIR."
    )
    assert texts.app_ready("0.1.0", "installed") == (
        "App dr-library 0.1.0 installed · backend ready"
    )
    assert texts.agent_server_failed("POST", "/api/x", "422", "bad") == (
        "✗ The agent-server refused POST /api/x (422): bad"
    )


def test_the_sentences_that_named_the_app_name_both_doors():
    """A browser user is not told to reinstall an app (TASK-48 V5)."""
    assert texts.NOTHING_INSTALLED == (
        "✗ Nothing is installed yet: start Deep Reasoning once (the app, or its browser "
        "command), then run this again."
    )
    assert texts.NO_AGENT_SERVER == (
        "✗ The after-ready phase needs AGENT_SERVER_URL and SESSION_API_KEY, which Deep "
        "Reasoning's launcher sets."
    )
    assert texts.state_from_a_newer_app("/h/setup.json", "2") == (
        "✗ /h/setup.json was written by a newer Deep Reasoning (its version 2; this one "
        "reads 1). Start the newer one again: the app, or its browser command. To set "
        "this one up from the start instead, delete /h/setup.json: your data stays, but a "
        "folder chosen with dr-app home is forgotten."
    )
    assert texts.state_unusable("/h/setup.json", "it is not JSON") == (
        "✗ /h/setup.json cannot be used: it is not JSON. Delete it and start Deep "
        "Reasoning again: setup then installs as on a first start, which needs the "
        "network. Your data stays, but a folder chosen with dr-app home must be chosen "
        "again."
    )
