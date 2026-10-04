import asyncio

from deep_reasoner import Func
from openai import APIConnectionError


def make(client, params):
    async def ask():
        return await client.chat.completions.create(
            model="any", messages=[{"role": "user", "content": "hi"}]
        )

    try:
        asyncio.run(ask())
    except APIConnectionError as exc:
        reached = f"{type(exc).__name__}: {exc}"
    else:
        reached = "the model answered"
    return Func(lambda: reached, description=reached)
