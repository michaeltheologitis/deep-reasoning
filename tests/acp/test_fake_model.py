import asyncio
import time

import openai
import pytest

from deep_reasoning.acp.testing.fake_model import FakeOpenAI, token_usage


async def ask(model, content):
    client = openai.AsyncOpenAI(
        base_url=model.base_url, api_key="unused", max_retries=0
    )
    try:
        return await client.chat.completions.create(
            model="m", messages=[{"role": "user", "content": content}]
        )
    finally:
        await client.close()


def test_answers_from_the_responder_and_records_each_call():
    async def body():
        async with FakeOpenAI(
            lambda messages: messages[-1]["content"].upper(), latency_s=0.1
        ) as model:
            before = time.time()
            replies = await asyncio.gather(ask(model, "one"), ask(model, "two"))
            return replies, model.calls, before, time.time()

    replies, calls, before, after = asyncio.run(body())
    assert sorted(r.choices[0].message.content for r in replies) == ["ONE", "TWO"]
    assert sorted(c.messages[-1]["content"] for c in calls) == ["one", "two"]
    assert all(before <= c.started <= after for c in calls)
    first, second = sorted(c.started for c in calls)
    assert second - first < 0.1, "the second call was served while the first waited"
    assert replies[0].usage.prompt_tokens > 0 and replies[0].usage.completion_tokens > 0


def test_a_responder_that_raises_answers_500():
    def broken(messages):
        raise RuntimeError("model down")

    async def body():
        async with FakeOpenAI(broken) as model:
            await ask(model, "hi")

    with pytest.raises(openai.InternalServerError, match="model down"):
        asyncio.run(body())


def test_token_counts_do_not_depend_on_where_the_code_is_installed():
    """Tracebacks in a prompt carry absolute paths, which differ between machines; the
    golden recordings hold the counts."""

    def frame(site: str) -> list[dict[str, str]]:
        line = f'File "{site}/deep_reasoner/repls/backends.py", line 522, in run_code'
        return [{"role": "user", "content": line}]

    here = frame("/home/user/site-packages")
    there = frame(
        "/home/runner/work/deep-reasoning/deep-reasoning/.venv/lib/site-packages"
    )
    assert token_usage(here, "ok") == token_usage(there, "ok")
    assert (
        token_usage(here + here, "ok")["prompt_tokens"]
        > token_usage(here, "ok")["prompt_tokens"]
    )
