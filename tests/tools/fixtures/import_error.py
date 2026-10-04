import yaml_x  # noqa: F401
from deep_reasoner import Func


def make(client, params):
    return Func(len, description="never built")
