"""The routes D4 adds to the App backend (D4 §7.2), behind D2's guard."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict
from starlette.requests import Request
from starlette.routing import Route

from deep_reasoning.library.api import _parse
from deep_reasoning.library.library import Library
from deep_reasoning.tools.check import check_tool


class CheckBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    yaml: str
    source: str | None = None
    example: str | None = None


Handler = Callable[[Request, bytes], Any]


def tool_routes(
    library: Library, route: Callable[[str, str, Handler], Route]
) -> list[Route]:
    """POST /tools/{name}/check (§7.2), built with D2's route."""

    def check(request: Request, body: bytes) -> Any:
        sent = _parse(CheckBody, body)
        name = request.path_params["name"]
        return check_tool(name, sent.yaml, sent.source, example=sent.example)

    return [
        route("/tools/{name}/check", "POST", check),
    ]
