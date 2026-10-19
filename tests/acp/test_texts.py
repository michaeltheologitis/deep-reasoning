import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.runlog import RecapNote


def test_sentences_with_fields_are_the_designs_verbatim():
    assert texts.late_decomposition("triage") == (
        "/triage starts a conversation with a decomposition, so it only works as the first "
        "message. Start a new conversation, or ask in plain words."
    )
    assert (
        texts.command_needs_task("triage", "the task")
        == "/triage needs a task after it: /triage <the task>"
    )
    assert (
        texts.namespace_fixed("router")
        == "namespace is fixed once a conversation has started (it is 'router')."
    )
    assert (
        texts.unknown_namespace("x", ["root", "router"])
        == "unknown namespace 'x'; this library has: root, router."
    )
    assert (
        texts.unknown_option("model")
        == "dr-acp has one option, 'namespace'; got 'model'."
    )
    assert texts.unknown_session("s-1") == "unknown session 's-1'."
    assert (
        texts.catalog_error("boom") == "dr-acp could not read its configuration: boom"
    )
    assert (
        texts.build_failed("ValueError: k") == "Could not start the run: ValueError: k"
    )
    assert texts.root_failed("ValueError: k") == (
        "The run failed: ValueError: k. Its REPL state is gone; your next message starts a fresh run."
    )
    assert texts.crashed(1, "/h/w.log") == (
        "The run crashed (exit code 1) and its REPL state is gone. Your next message starts a "
        "fresh run. The worker's log is /h/w.log."
    )
    assert texts.child_failed("ValueError: boom") == "Failed: ValueError: boom"
    assert texts.cell_interrupted("the run crashed") == "Not finished: the run crashed"


@pytest.mark.parametrize(
    ("after", "recap", "notice"),
    [
        ("stopped", None, texts.FRESH_AFTER_STOP),
        (
            "stopped",
            RecapNote(turns=2, left_out=0, shortened=False),
            (
                "Starting a fresh run: the previous one was stopped, so its variables and "
                "sub-agents are gone. This run is given your earlier messages and their "
                "answers."
            ),
        ),
        (
            "lost",
            RecapNote(turns=14, left_out=6, shortened=True),
            (
                "Starting a fresh run: the previous one ended when dr-acp restarted, so its "
                "variables and sub-agents are gone. This run is given your messages from "
                "message 7 on, and their answers: older ones are left out to fit the "
                "model's context. Any message or answer longer than 4,000 characters is cut "
                "short."
            ),
        ),
        (
            "closed",
            RecapNote(turns=1, left_out=0, shortened=True),
            (
                "Starting a fresh run: the previous one was closed, so its variables and "
                "sub-agents are gone. This run is given your earlier messages and their "
                "answers. Any message or answer longer than 4,000 characters is cut short."
            ),
        ),
        ("build_failed", RecapNote(turns=1, left_out=0, shortened=False), None),
    ],
    ids=["before_task_57", "stopped", "lost_left_out", "closed_cut", "build_failed"],
)
def test_a_fresh_run_says_what_it_is_given(after, recap, notice):
    assert texts.fresh_run_notice(after, recap) == notice


@pytest.mark.parametrize(
    ("mode", "backbone", "sentence"),
    [
        (
            "interim",
            "chat",
            "Stop requested: this agent and its sub-agents stop at their next turn, before their next model call. A cell that is already running finishes first.",
        ),
        (
            "dean",
            "chat",
            "Stop requested: this agent and its sub-agents stop at their next turn, before their next model call. A cell that is already running finishes first.",
        ),
        (
            "interim",
            "claude_code",
            "Stop requested: this agent runs a Claude Code session, which is one turn, so it stops when that session ends.",
        ),
        (
            "dean",
            "claude_code",
            "Stop requested: its Claude Code session is being ended.",
        ),
    ],
)
def test_a_stop_request_says_when_it_lands(mode, backbone, sentence):
    assert texts.stop_requested(mode, backbone) == sentence


def test_the_key_proxys_sentences_are_d5s_verbatim():
    assert texts.cap_reached(0.008, 5) == (
        "The key proxy refused this model call: this conversation has spent $0.01 of "
        "its $5.00 cap. Start a new conversation, or raise the cap (--spend-cap-usd in "
        "the deep_reasoner agent profile's arguments)."
    )
    assert texts.unpriced("m-x", "/h") == (
        "The key proxy refused a call to 'm-x': its price is unknown, so the spend cap "
        "cannot bound it. Add it to /h/prices.yaml (input and output USD per million "
        "tokens), then send your message again."
    )
    assert texts.not_a_model_call("embeddings", "GET", "files") == (
        "The key proxy forwards only model calls (embeddings); GET /files was refused."
    )
    assert texts.BAD_TOKEN == "The key proxy does not know this token."
    assert texts.upstream_unreachable("api.openai.com", "refused") == (
        "The key proxy could not reach api.openai.com: refused."
    )
