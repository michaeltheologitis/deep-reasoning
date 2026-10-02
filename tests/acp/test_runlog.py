import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from deep_reasoning.acp.costs import CostLedger
from deep_reasoning.acp.runlog import (
    Home,
    RunEnd,
    RunLog,
    SessionIndex,
    StopRequest,
    Thought,
)

RUN = "20261002-142233-4f1a2b"


def test_appends_are_numbered_without_gaps_and_read_back_in_order(tmp_path):
    home = Home(tmp_path)
    log = RunLog.create(home, RUN)
    written = [log.append(Thought(node=1, text="a")), log.append(StopRequest(node=2))]
    assert [e.seq for e in written] == [1, 2]
    assert all(e.t > 0 for e in written)
    assert list(RunLog.read(home, RUN)) == written
    assert (home.run_dir(RUN) / "events.jsonl").read_text().count("\n") == 2


def test_an_existing_log_continues_its_numbering(tmp_path):
    home = Home(tmp_path)
    RunLog.create(home, RUN).append(Thought(node=1, text="a"))
    ended = RunLog.open(home, RUN).append(
        RunEnd(reason="lost", exit_code=None, detail=None)
    )
    assert ended.seq == 2
    assert [e.kind for e in RunLog.read(home, RUN)] == ["thought", "run.end"]


def test_a_log_of_another_version_is_refused(tmp_path):
    home = Home(tmp_path)
    home.run_dir(RUN).mkdir(parents=True)
    (home.run_dir(RUN) / "events.jsonl").write_text(
        json.dumps({"v": 2, "kind": "thought", "node": 1, "text": "a"}) + "\n"
    )
    with pytest.raises(ValidationError):
        list(RunLog.read(home, RUN))


def test_home_is_the_flag_then_dr_home_then_the_users(monkeypatch, tmp_path):
    monkeypatch.setenv("DR_HOME", str(tmp_path / "env"))
    assert Home.resolve(tmp_path / "flag").root == tmp_path / "flag"
    assert Home.resolve(None).root == tmp_path / "env"
    monkeypatch.delenv("DR_HOME")
    monkeypatch.setenv("HOME", str(tmp_path / "user"))
    assert Home.resolve(None).root == tmp_path / "user" / ".deep-reasoning"
    assert Home(Path("/h")).session_file("s-1") == Path("/h/sessions/s-1.json")
    assert Home(Path("/h")).run_dir(RUN) == Path(f"/h/runs/{RUN}")


def test_the_session_index_round_trips_in_the_designs_shape(tmp_path):
    home = Home(tmp_path)
    index = SessionIndex(
        session="s-7c1f9e0a2b4d6e8f",
        cwd="/workspace",
        namespace="router",
        started=True,
        source={"kind": "config", "config_path": "/abs/main.yaml"},
        runs=[RUN],
        cost=CostLedger(usd=0.0041, tokens_in=9120, tokens_out=1388),
        last_end="stopped",
        created=datetime(2026, 10, 2, 14, 22, 31, tzinfo=UTC),
    )
    index.save(home)
    assert SessionIndex.load(home, "s-7c1f9e0a2b4d6e8f") == index
    assert json.loads(home.session_file("s-7c1f9e0a2b4d6e8f").read_text()) == {
        "v": 1,
        "session": "s-7c1f9e0a2b4d6e8f",
        "cwd": "/workspace",
        "namespace": "router",
        "started": True,
        "source": {"kind": "config", "config_path": "/abs/main.yaml"},
        "runs": [RUN],
        "cost": {
            "usd": 0.0041,
            "complete": True,
            "tokens_in": 9120,
            "tokens_out": 1388,
        },
        "last_end": "stopped",
        "created": "2026-10-02T14:22:31Z",
    }
    assert list(home.root.joinpath("sessions").iterdir()) == [
        home.session_file("s-7c1f9e0a2b4d6e8f")
    ]
    assert SessionIndex.load(home, "s-unknown") is None
