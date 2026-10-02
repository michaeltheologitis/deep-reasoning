"""A live run: the worker process, its two pipes, the pump (§4.2, §6.4)."""

from typing import TYPE_CHECKING, Literal

from deep_reasoning.acp.catalog import RunSource
from deep_reasoning.acp.encoder import ChildRef, Encoder
from deep_reasoning.acp.route import ModelRoute
from deep_reasoning.acp.runlog import Home, Mode, PromptEnd, RunEnd, RunEndReason
from deep_reasoning.acp.wire import Outbox

if TYPE_CHECKING:
    from deep_reasoning.acp.session import Session


class RunHandle:
    run_id: str
    encoder: Encoder

    @classmethod
    async def start(
        cls,
        *,
        run_id: str,
        session: "Session",
        source: RunSource,
        after: RunEndReason | None,
        home: Home,
        route: ModelRoute,
        outbox: Outbox,
        mode: Mode,
        heartbeat_s: float,
    ) -> "RunHandle":
        """Create the run's log and worker, and start its pump and heartbeat.

        RunLog.create; append run.start (with after); grant = route.grant(session=...,
        run=run_id, upstream=source.client); spawn the worker: sys.executable -m
        deep_reasoning.acp.worker --control-fd C --events-fd E, pass_fds=(C, E),
        start_new_session=True, stdin=DEVNULL, stdout and stderr to runs/<run>/worker.log,
        cwd=session.cwd, env=worker_env(os.environ, grant); send
        Start(client_overrides=grant.client_overrides, ...).
        """
        raise NotImplementedError

    async def prompt(
        self, index: int, text: str, task: str, decomposition: str | None
    ) -> PromptEnd | RunEnd:
        """Log prompt.start, send Prompt, return the event that ended the prompt: its
        prompt.end, or the run.end of a run stopped, closed or crashed under it.

        After a failed or build_failed outcome, return only once run.end is logged.
        """
        raise NotImplementedError

    def stop_node(self, node: int) -> None:
        """Log stop.request and send Stop; return at once."""
        raise NotImplementedError

    async def kill(self, reason: Literal["stopped", "closed"]) -> None:
        """End the worker's process group (§6.4). Idempotent."""
        raise NotImplementedError

    async def close(self, grace_s: float = 2.0) -> None:
        """Send Close; kill("closed") if the worker has not exited after grace_s."""
        raise NotImplementedError

    def child(self, session_id: str) -> ChildRef | None:
        """The live child with this session id, for cancel routing."""
        raise NotImplementedError
