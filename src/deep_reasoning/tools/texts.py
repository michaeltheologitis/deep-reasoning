"""Every sentence Check and the tool routes can send, verbatim from D4 §9.1.

A constant is a sentence without fields; a function returns the sentence with its fields.
"""

BUILT = "builds"


def reserved_name(name: str) -> str:
    return (
        f"'{name}' is one of deep_reasoner's own names in the REPL (subagent, run_all, "
        "FinalAnswer, Var, Func, task); a tool by that name would hide it. Choose another "
        "name."
    )


def syntax(name: str, line: int | None, message: str) -> str:
    return f"tool '{name}': tools/{name}.py line {line}: {message}"


def factory_raised(name: str, factory: str, type_name: str, message: str) -> str:
    return f"tool '{name}': {factory} raised {type_name}: {message}"


def build_timeout(name: str, seconds: float) -> str:
    return (
        f"tool '{name}': building it took longer than {seconds:g} s, so Check stopped it. "
        "A tool is built at the start of every conversation; a factory must return "
        "quickly."
    )


def ready_timeout(seconds: float) -> str:
    return (
        f"Check could not start deep_reasoner within {seconds:g} s, so it did not build "
        "the tool. Try again."
    )


def child_ended(name: str, how: str, phase: str) -> str:
    """how: 'exit code 3', 'signal 11'; phase: 'starting', 'building the tool'."""
    return f"tool '{name}': the Check process ended ({how}) while {phase}."


def example_timeout(seconds: float) -> str:
    return f"TimeoutError: the expression did not finish within {seconds:g} s"


def builtin(factory: str) -> str:
    return (
        f"'{factory}' is one of deep_reasoner's own factories. It is built when a "
        "conversation starts, with your model and files, so Check does not build it here."
    )


def check_failed(name: str) -> str:
    return f"'{name}' did not pass Check, so it was not saved."


def mcp_via_grant(name: str) -> str:
    return f"'{name}' is an MCP server's grant: change it in the MCP servers list."


def mcp_server_taken(server: str, other: str) -> str:
    return f"MCP server '{server}' is already granted as '{other}'."


def mcp_name_taken(name: str) -> str:
    """The frame's MCP_NAME_TAKEN (§9.3), for a grant over a tool of your own."""
    return f"A tool named '{name}' exists: choose another name."


MCP_NEEDS_COMMAND = "A stdio MCP server needs a command."
MCP_NEEDS_URL = "An HTTP or SSE MCP server needs a URL."
MCP_BAD_REQUEST = (
    "The body must be a JSON object with 'server', 'transport', 'granted_in' and "
    "'base_version', and may have 'command', 'args', 'url', 'env' and 'headers'."
)
