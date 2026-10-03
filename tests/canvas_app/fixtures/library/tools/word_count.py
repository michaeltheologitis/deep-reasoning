"""A tool of our own for the panel's fixture Library."""

from deep_reasoner.primitives import Func


def make(client, params):
    return Func(
        lambda text: len(text.split()), description="word_count(text): words in text"
    )
