import json
import os
import threading
import time
from contextlib import closing

import pytest
import yaml
from fake_model import FakeOpenAI, repl, scripted, task_and_turn
from genai_prices import Usage, calc_price

from deep_reasoning import runs as runs_module
from deep_reasoning.library import (
    default_namespace,
    engine_config,
    import_config,
    open_library,
)
from deep_reasoning.runs import (
    LOST,
    TOO_LONG,
    RunInProgress,
    Runs,
    Turn,
    end_unfinished,
    read_turn,
)

pytestmark = pytest.mark.anyio

CHAT = "a-chat"
HELD_S = 30
FAN_OUT = {
    "Summarize two courses.": [
        repl(
            "r = run_all({c: anext(subagent().send(f'Summarize {c}.')) for c in ['C1', 'C2']})",
            "print(r)",
            think="Fan out.",
        ),
        repl("FinalAnswer(r)"),
    ],
    "Summarize C1.": [repl("print('C1 has 3 credits')"), repl("FinalAnswer('C1: 3')")],
    "Summarize C2.": [repl("FinalAnswer('C2: 4')", think="Easy.")],
}
FAN_OUT_ANSWER = "{'C1': 'C1: 3', 'C2': 'C2: 4'}"
PRINT_GROUP = repl("import os", "print(os.getpgrp())")


async def run_to_the_end(runs, prompt, config, earlier=()):
    run = runs.start(CHAT, prompt, config, earlier)
    return run, [event async for event in runs.events(run)]


def of_kind(events, kind):
    return [event for event in events if event["kind"] == kind]


def group_of(events):
    """The worker's process group, which the run's first cell printed."""
    return int(of_kind(events, "cell.end")[0]["output"])


async def stop_at(runs, run, code):
    """Every event of the run, stopping it once a cell running *code* starts; and the
    seconds from the stop to the run's end."""
    events, stopped_at = [], None
    async for event in runs.events(run):
        events.append(event)
        if event["kind"] == "cell.start" and event["code"] == code:
            stopped_at = time.monotonic()
            assert runs.stop(run)
    return events, time.monotonic() - stopped_at


async def test_a_fan_out_streams_one_tree_in_order(home, fake_config):
    with FakeOpenAI(scripted(FAN_OUT)) as fake:
        run, events = await run_to_the_end(
            Runs(home), "Summarize two courses.", fake_config(fake)
        )
    assert [event["seq"] for event in events] == list(range(1, len(events) + 1))
    assert events[0]["kind"] == "turn.start" and events[-1]["kind"] == "turn.end"
    starts = {event["node"]: event for event in of_kind(events, "agent.start")}
    fan_out = of_kind(events, "cell.start")[0]
    assert fan_out["node"] == 1
    assert [starts[node]["parent"] for node in (1, 2, 3)] == [None, 1, 1]
    assert starts[2]["cell"] == starts[3]["cell"] == fan_out["cell"]
    results = {event["node"]: event["result"] for event in of_kind(events, "agent.end")}
    assert results == {1: FAN_OUT_ANSWER, 2: "C1: 3", 3: "C2: 4"}
    fan_out_end = next(
        e for e in of_kind(events, "cell.end") if e["cell"] == fan_out["cell"]
    )
    child_ends = [e["seq"] for e in of_kind(events, "agent.end") if e["node"] != 1]
    assert fan_out["seq"] < starts[2]["seq"] and max(child_ends) < fan_out_end["seq"]
    assert events[-1]["outcome"] == "answered"
    assert events[-1]["answer"] == FAN_OUT_ANSWER
    logged = (home / "runs" / run / "events.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in logged] == events


async def test_stop_ends_every_agent_and_cell_stopped(home, fake_config):
    spin = repl("while True:", "    pass")
    plan = {
        "Keep a spinner going.": [PRINT_GROUP, repl("print(subagent('Spin.'))")],
        "Spin.": [spin],
    }
    with FakeOpenAI(scripted(plan)) as fake:
        runs = Runs(home)
        run = runs.start(CHAT, "Keep a spinner going.", fake_config(fake), [])
        events, seconds = await stop_at(runs, run, "while True:\n    pass")
    assert seconds < 2
    ends = {event["node"]: event["status"] for event in of_kind(events, "agent.end")}
    assert ends == {1: "stopped", 2: "stopped"}
    cell_ends = {
        event["cell"]: event["status"] for event in of_kind(events, "cell.end")
    }
    assert cell_ends == {1: "done", 2: "stopped", 3: "stopped"}
    assert events[-1]["outcome"] == "stopped"
    with pytest.raises(ProcessLookupError):
        os.killpg(group_of(events), 0)


async def test_stop_kills_a_cell_blocked_in_c(home, fake_config):
    plan = {"Wait a minute.": [PRINT_GROUP, repl("import time", "time.sleep(60)")]}
    with FakeOpenAI(scripted(plan)) as fake:
        runs = Runs(home, stop_grace_s=0.5)
        run = runs.start(CHAT, "Wait a minute.", fake_config(fake), [])
        events, seconds = await stop_at(runs, run, "import time\ntime.sleep(60)")
    assert seconds < 3
    assert of_kind(events, "agent.end") == []
    assert events[-1]["outcome"] == "stopped"
    with pytest.raises(ProcessLookupError):
        os.killpg(group_of(events), 0)


async def test_stop_before_the_root_starts_calls_no_model(home, fake_config):
    with FakeOpenAI(scripted(FAN_OUT)) as fake:
        runs = Runs(home)
        run = runs.start(CHAT, "Summarize two courses.", fake_config(fake), [])
        assert runs.stop(run)
        events = [event async for event in runs.events(run)]
    assert fake.calls == []
    assert [event["status"] for event in of_kind(events, "agent.end")] == ["stopped"]
    assert events[-1]["outcome"] == "stopped" and events[-1]["cost"] == 0


async def test_each_call_is_priced_from_its_usage(home, fake_config):
    usage = {
        "prompt_tokens": 10_000,
        "completion_tokens": 2_000,
        "total_tokens": 12_000,
        "prompt_tokens_details": {"cached_tokens": 8_000},
    }
    tokens = Usage(input_tokens=10_000, cache_read_tokens=8_000, output_tokens=2_000)
    price = float(calc_price(tokens, "gpt-6-luna").total_price)
    with FakeOpenAI(scripted(FAN_OUT), usage=lambda messages, reply: usage) as fake:
        _, events = await run_to_the_end(
            Runs(home), "Summarize two courses.", fake_config(fake)
        )
    costs = [event["cost"] for event in of_kind(events, "usage")]
    assert costs == [pytest.approx(price)] * len(fake.calls)
    assert events[-1]["cost"] == pytest.approx(price * len(fake.calls))


async def test_an_unknown_models_calls_cost_null_not_zero(home, fake_config):
    with FakeOpenAI(scripted(FAN_OUT)) as fake:
        config = fake_config(fake, model="a-model-nobody-prices")
        _, events = await run_to_the_end(Runs(home), "Summarize two courses.", config)
    assert {event["cost"] for event in of_kind(events, "usage")} == {None}
    assert events[-1]["cost"] is None


async def test_a_follow_up_gets_every_earlier_turn_whole(home, fake_config):
    question = "Repeat this back: " + " ".join(["word"] * 5_000)
    answer = "x" * 20_000
    plan = {
        "Repeat this back": [repl(f"FinalAnswer('x' * {len(answer)})")],
        "What did I ask first?": [repl("FinalAnswer('that')")],
    }
    with FakeOpenAI(scripted(plan)) as fake:
        runs = Runs(home)
        first, _ = await run_to_the_end(runs, question, fake_config(fake))
        earlier = [read_turn(home, first)]
        _, events = await run_to_the_end(
            runs, "What did I ask first?", fake_config(fake), earlier
        )
    messages = fake.calls[1].messages
    assert [message["role"] for message in messages] == ["system", "user", "user"]
    assert f"Message 1: {question}\nAnswer 1: {answer}\n" in messages[1]["content"]
    assert messages[2]["content"] == "What did I ask first?"
    assert of_kind(events, "agent.start")[0]["task"] == "What did I ask first?"


async def test_after_a_stop_the_next_message_is_sent_alone(home, fake_config):
    plan = {"Try again, briefly.": [repl("FinalAnswer('ok')")]}
    with FakeOpenAI(scripted(plan)) as fake:
        runs = Runs(home)
        stopped = runs.start(CHAT, "Count the stars.", fake_config(fake), [])
        runs.stop(stopped)
        _ = [event async for event in runs.events(stopped)]
        earlier = [read_turn(home, stopped)]
        await run_to_the_end(runs, "Try again, briefly.", fake_config(fake), earlier)
    texts = [message["content"] for message in fake.calls[0].messages]
    assert sum(text.count("Count the stars.") for text in texts) == 1
    stopped_turn = (
        "Message 1: Count the stars.\n"
        "Answer 1: (none: the user stopped the run before it answered)"
    )
    assert stopped_turn in texts[-2]
    assert texts[-1] == "Try again, briefly."


async def test_turns_survive_a_restart(home, fake_config):
    with FakeOpenAI(scripted(FAN_OUT)) as fake:
        run, events = await run_to_the_end(
            Runs(home), "Summarize two courses.", fake_config(fake)
        )
    restarted = Runs(home)
    assert read_turn(home, run) == Turn(
        "Summarize two courses.", "answered", FAN_OUT_ANSWER, None
    )
    assert [event async for event in restarted.events(run)] == events


async def test_a_dead_worker_ends_the_turn_failed(home, fake_config):
    plan = {"Crash.": [repl("import os", "os._exit(3)")]}
    with FakeOpenAI(scripted(plan)) as fake:
        run, events = await run_to_the_end(Runs(home), "Crash.", fake_config(fake))
    assert events[-1]["outcome"] == "failed"
    assert "exited with code 3" in events[-1]["detail"]
    assert str(home / "runs" / run / "worker.log") in events[-1]["detail"]


async def test_a_stream_rejoined_mid_run_replays_without_gaps(home, fake_config):
    release = threading.Event()
    follow = scripted(FAN_OUT)

    def held_before_answering(messages):
        if task_and_turn(messages) == ("Summarize two courses.", 1):
            release.wait(HELD_S)
        return follow(messages)

    with FakeOpenAI(held_before_answering) as fake:
        runs = Runs(home)
        run = runs.start(CHAT, "Summarize two courses.", fake_config(fake), [])
        stream = runs.events(run)
        seen = [await anext(stream) for _ in range(5)]
        rejoined = runs.events(run, after=3)
        replay = [await anext(rejoined)]
        release.set()
        seen += [event async for event in stream]
        replay += [event async for event in rejoined]
    assert seen[-1]["kind"] == "turn.end"
    assert replay == seen[3:]


async def test_a_chat_runs_one_message_at_a_time(home, fake_config):
    release = threading.Event()
    follow = scripted(FAN_OUT)

    def held(messages):
        release.wait(HELD_S)
        return follow(messages)

    with FakeOpenAI(held) as fake:
        runs = Runs(home)
        run = runs.start(CHAT, "Summarize two courses.", fake_config(fake), [])
        with pytest.raises(RunInProgress):
            runs.start(CHAT, "And another thing.", fake_config(fake), [])
        assert runs.live(CHAT) == run
        release.set()
        _ = [event async for event in runs.events(run)]
    assert runs.live(CHAT) is None


async def test_an_event_too_long_to_read_ends_the_turn_failed(
    home, fake_config, monkeypatch
):
    monkeypatch.setattr(runs_module, "LINE_LIMIT", 64 * 1024)
    plan = {"Shout.": [repl("print('x' * 100_000)")]}
    with FakeOpenAI(scripted(plan)) as fake:
        _, events = await run_to_the_end(Runs(home), "Shout.", fake_config(fake))
    assert events[-1]["outcome"] == "failed"
    assert events[-1]["detail"] == TOO_LONG


async def test_long_outputs_and_answers_arrive_whole(home, fake_config):
    plan = {
        "Write a lot.": [
            repl("text = 'x' * 1_000_000", "print(text)"),
            repl("FinalAnswer(text)"),
        ]
    }
    with FakeOpenAI(scripted(plan)) as fake:
        _, events = await run_to_the_end(Runs(home), "Write a lot.", fake_config(fake))
    assert of_kind(events, "cell.end")[0]["output"] == "x" * 1_000_000
    assert events[-1]["answer"] == "x" * 1_000_000


def test_a_run_the_app_stopped_under_is_ended_failed(home):
    run = "20261025-120000-000000"
    folder = home / "runs" / run
    folder.mkdir(parents=True)
    started = {"seq": 1, "t": 100.0, "kind": "turn.start", "prompt": "Hi."}
    used = {"seq": 2, "t": 101.5, "kind": "usage", "node": 1, "cost": 0.25}
    lines = [json.dumps(started), json.dumps(used)]
    (folder / "events.jsonl").write_text("\n".join(lines) + "\n")
    assert end_unfinished(home) == [run]
    assert end_unfinished(home) == []
    assert read_turn(home, run) == Turn("Hi.", "failed", None, LOST)
    last = json.loads((folder / "events.jsonl").read_text().splitlines()[-1])
    assert (last["seq"], last["cost"], last["seconds"]) == (3, 0.25, 1.5)


COURSES = {
    "CS": {
        "CS101": {"credits": 4, "year": 1},
        "CS102": {"credits": 4, "year": 1},
        "CS201": {"credits": 4, "year": 2},
    },
    "STAT": {
        "STAT101": {"credits": 3, "year": 1},
        "STAT201": {"credits": 3, "year": 2},
    },
}
FIRST_QUESTION = (
    "Which department is lighter for a first-year student, CS or STAT? Give each "
    "department to its own sub-agent to total its first-year credits from `courses`, "
    "then compare the totals."
)


@pytest.mark.live
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="no OPENAI_API_KEY")
async def test_gpt_6_luna_on_the_librarys_defaults_answers_and_remembers_the_chat(
    home, library, tmp_path
):
    """The app's part on a real model: a run that answers through sub-agents, every call
    priced, and a follow-up that is given the chat so far. Not the model's reasoning."""
    courses = tmp_path / "courses.yaml"
    courses.write_text(
        yaml.safe_dump({"namespaces": {"root": {"vars": {"courses": COURSES}}}})
    )
    with closing(open_library(library)) as connection:
        import_config(connection, courses)

    def config_for(folder):
        return engine_config(library, default_namespace(library), folder / "tools")

    runs = Runs(home)
    first, events = await run_to_the_end(runs, FIRST_QUESTION, config_for)
    assert events[-1]["outcome"] == "answered", events[-1]
    assert any(event["parent"] for event in of_kind(events, "agent.start"))
    costs = [event["cost"] for event in of_kind(events, "usage")]
    assert costs and None not in costs
    assert events[-1]["cost"] == pytest.approx(sum(costs))
    earlier = [read_turn(home, first)]
    _, follow_up = await run_to_the_end(
        runs, "Quote my first question word for word.", config_for, earlier
    )
    assert follow_up[-1]["outcome"] == "answered", follow_up[-1]
    assert "first-year" in follow_up[-1]["answer"]
    print(
        f"\nfirst: {events[-1]['answer']!r} (${events[-1]['cost']:.6f}, "
        f"{len(costs)} calls, {len(of_kind(events, 'agent.start'))} agents, "
        f"{events[-1]['seconds']} s)\nfollow-up: {follow_up[-1]['answer']!r} "
        f"(${follow_up[-1]['cost']:.6f})"
    )
