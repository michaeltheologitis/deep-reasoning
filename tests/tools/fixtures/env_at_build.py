import os

from deep_reasoner import Func


def make(client, params):
    token = os.environ["D4_TOKEN"]
    return Func(lambda: token, description="the token")
