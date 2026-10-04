from deep_reasoner import Func


def make(client, params):
    print("x" * 1_000_000)
    print("the end of what the tool printed")
    return Func(len, description="length")
