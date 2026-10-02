from importlib.metadata import version


def test_installed_acp_is_the_pinned_0_12_1():
    assert version("agent-client-protocol") == "0.12.1"
