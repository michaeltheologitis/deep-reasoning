from dr_app import texts


def test_sentences_with_fields_are_the_designs_verbatim():
    assert texts.safety("5") == (
        "deep_reasoner runs as you. It can read and change any file you can, and code it "
        "writes can find your model keys on this computer if it tries. Spend through the "
        "key proxy stops at $5 per conversation."
    )
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
        "installing deep-reasoning a1b2c3d with deep_reasoner d7334ae … (first launch, "
        "or after an update: a few minutes)"
    )
    assert texts.install_failed("a1b2c3d", "uv sync", "2") == (
        "✗ Installing deep-reasoning a1b2c3d failed (uv sync exited 2); its output is "
        "above. After an update this needs the network once: connect and restart."
    )
