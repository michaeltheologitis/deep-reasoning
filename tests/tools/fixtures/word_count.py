from deep_reasoner import Func


def make(client, params):
    def word_count(text: str) -> int:
        """Count the words in text."""
        return len(text.split())

    return Func(
        word_count, description="word_count(text) -> int: number of words in text."
    )


def make_broken(client, params):
    return len
