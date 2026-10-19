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
