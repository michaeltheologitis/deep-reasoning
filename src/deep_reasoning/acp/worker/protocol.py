"""Control messages, front -> worker, one JSON object per line (§4.3)."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter


class Start(BaseModel):
    op: Literal["start"] = "start"
    run: str
    session: str
    run_dir: str
    config_path: str
    namespace: str
    client_overrides: dict[str, Any]  # merged over cfg.client


class Prompt(BaseModel):
    op: Literal["prompt"] = "prompt"
    prompt: int  # 1-based within the run
    task: str  # the text without its slash command
    decomposition: str | None  # the command's decomposition, first prompt only


class Stop(BaseModel):
    op: Literal["stop"] = "stop"
    node: int


class Close(BaseModel):
    op: Literal["close"] = "close"


Control = Annotated[Start | Prompt | Stop | Close, Field(discriminator="op")]
CONTROL: TypeAdapter[Control] = TypeAdapter(Control)
