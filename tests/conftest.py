import importlib
import sys

# juplit.test() is true in any process that has imported pytest, so deep_reasoner's
# modules would run their notebook tests when first imported here. Import them once with
# pytest out of sight.
_pytest = sys.modules.pop("pytest")
try:
    for module in (
        "deep_reasoner.v2.cli",
        "deep_reasoner.mocks",
        "deep_reasoner.v2.decompositions",
        "deep_reasoner.v2.messages",
    ):
        importlib.import_module(module)
finally:
    sys.modules["pytest"] = _pytest
