"""Hand-written update streams, shaped as dr-acp sends them (§5.2, §5.3)."""

from typing import Any

R1 = "20261002-162835-3fa9c1"
R2 = "20261002-163410-8b2e07"
ROOT = "s-7c1f9e0a2b4d6e8f"
OTHER_ROOT = "s-0d93b27e5a1c4f68"

Update = tuple[str, dict[str, Any]]


def text(t: str) -> dict[str, Any]:
    return {"type": "text", "text": t}


def cell(
    session: str, run: str, node: int, k: int, code: str, parent: int | None = None
) -> Update:
    depth = 1 if parent is None else 2
    return (
        session,
        {
            "sessionUpdate": "tool_call",
            "toolCallId": f"{run}-n{node}-c{k}",
            "title": f"Run {code.splitlines()[0]}" + (" …" if "\n" in code else ""),
            "kind": "execute",
            "status": "in_progress",
            "rawInput": {"command": code},
            "_meta": {
                "deep_reasoner": {
                    "run": run,
                    "node": node,
                    "parent": parent,
                    "depth": depth,
                    "cell": k,
                    "origin": "think",
                }
            },
        },
    )


def done(
    session: str, run: str, node: int, k: int, output: str, status: str = "completed"
) -> Update:
    return (
        session,
        {
            "sessionUpdate": "tool_call_update",
            "toolCallId": f"{run}-n{node}-c{k}",
            "status": status,
            "content": [{"type": "content", "content": text(output)}],
            "rawOutput": output,
        },
    )


def dr(
    run: str, node: int, parent: int, drive: int = 1, **outcome: Any
) -> dict[str, Any]:
    return {
        "run": run,
        "node": node,
        "parent": parent,
        "depth": 2,
        "namespace": "advising",
        "backbone": "chat",
        "drive": drive,
        **outcome,
    }


def announce(
    parent_session: str,
    run: str,
    node: int,
    parent: int,
    k: int,
    title: str,
    drive: int = 1,
) -> Update:
    return (
        parent_session,
        {
            "sessionUpdate": "subagent_update",
            "sessionId": f"{run}-n{node}",
            "title": title,
            "capabilities": {"cancel": {}},
            "state": {"state": "running"},
            "_meta": {
                "openhands": {"parentToolCallId": f"{run}-n{parent}-c{k}"},
                "deep_reasoner": dr(run, node, parent, drive),
            },
        },
    )


def idle(
    parent_session: str,
    run: str,
    node: int,
    parent: int,
    k: int,
    reason: str | None,
    **outcome: Any,
) -> Update:
    state = {"state": "idle", **({"stopReason": reason} if reason else {})}
    return (
        parent_session,
        {
            "sessionUpdate": "subagent_update",
            "sessionId": f"{run}-n{node}",
            "state": state,
            "_meta": {
                "openhands": {"parentToolCallId": f"{run}-n{parent}-c{k}"},
                "deep_reasoner": dr(run, node, parent, **outcome),
            },
        },
    )


def message(sender: str, recipient: str, message_id: str, body: str) -> Update:
    return (
        sender,
        {
            "sessionUpdate": "session_message",
            "messageId": message_id,
            "senderSessionId": sender,
            "recipientSessionId": recipient,
            "content": [text(body)],
        },
    )


def usage(session: str, amount: float | None) -> Update:
    update: dict[str, Any] = {
        "sessionUpdate": "usage_update",
        "used": 10,
        "size": 100,
        "_meta": {
            "deep_reasoner": {
                "cost_source": "table",
                "tokens_in": 1,
                "tokens_out": 1,
                "unknown_calls": 0 if amount is not None else 1,
            }
        },
    }
    if amount is not None:
        update["cost"] = {"amount": amount, "currency": "USD"}
    return (session, update)


def closing(
    root: str, run: str | None, prompt: int | None, outcome: str, body: str
) -> Update:
    return (
        root,
        {
            "sessionUpdate": "agent_message_chunk",
            "content": text(body),
            "_meta": {
                "deep_reasoner": {"run": run, "prompt": prompt, "outcome": outcome}
            },
        },
    )


def notice(root: str, body: str) -> Update:
    return (
        root,
        {"sessionUpdate": "agent_message_chunk", "content": text(body + "\n\n")},
    )


def card(run: str, node: int, parent: int, k: int, title: str, path: str) -> Update:
    return (
        ROOT,
        {
            "sessionUpdate": "tool_call",
            "toolCallId": f"{run}-n{node}-a1",
            "title": f"{path} · {title}",
            "kind": "other",
            "status": "in_progress",
            "rawInput": {"task": title},
            "_meta": {
                "openhands": {"parentToolCallId": f"{run}-n{parent}-c{k}"},
                "deep_reasoner": dr(run, node, parent),
            },
        },
    )


def card_done(
    run: str, node: int, call_status: str, body: str, **outcome: Any
) -> Update:
    return (
        ROOT,
        {
            "sessionUpdate": "tool_call_update",
            "toolCallId": f"{run}-n{node}-a1",
            "status": call_status,
            "content": [{"type": "content", "content": text(body)}],
            "_meta": {"deep_reasoner": {"run": run, "node": node, **outcome}},
        },
    )


def child_session(run: str, node: int) -> str:
    return f"{run}-n{node}"


N2 = child_session(R1, 2)
N3 = child_session(R1, 3)


def native_run() -> list[Update]:
    """Root fans out n2 and n3 in c1.1; n2 answers, n3 fails; the root answers."""
    return [
        cell(ROOT, R1, 1, 1, "found = run_all(...)\nprint(found)"),
        announce(ROOT, R1, 2, 1, 1, "Summarize the CS department."),
        message(ROOT, N2, f"{N2}-t1", "Summarize the CS department."),
        announce(ROOT, R1, 3, 1, 1, "Summarize the STAT department."),
        cell(N2, R1, 2, 1, "print(cs)", parent=1),
        done(N2, R1, 2, 1, "['CS101', 'CS102']"),
        usage(N2, 0.0004),
        message(N2, ROOT, f"{N2}-r1", "CS is heavy."),
        usage(N2, 0.0037),
        idle(ROOT, R1, 2, 1, 1, "end_turn", status="done"),
        usage(N3, None),
        idle(
            ROOT,
            R1,
            3,
            1,
            1,
            "end_turn",
            status="failed",
            detail="ValueError: the catalog has no STAT section at all",
        ),
        done(ROOT, R1, 1, 1, "{'CS': 'CS is heavy.'}"),
        cell(ROOT, R1, 1, 2, "FinalAnswer('STAT is lighter.')"),
        done(ROOT, R1, 1, 2, "FinalAnswer: 'STAT is lighter.'"),
        closing(ROOT, R1, 1, "answered", "STAT is lighter."),
        usage(ROOT, 0.0089),
    ]
