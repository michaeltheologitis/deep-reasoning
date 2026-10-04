"""The key proxy and the spend cap, in process: httpx in front, a fake upstream behind
(D5 §4.7, §7.1)."""

import asyncio
import json
import logging
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Self

import httpx
import openai
import pytest

from deep_reasoning.acp import texts
from deep_reasoning.acp.costs import Price, PriceTable
from deep_reasoning.acp.proxy import (
    KeyProxy,
    ProxyRoute,
    SpendLedger,
    loopback_proxy_env,
)
from deep_reasoning.acp.route import RouteGrant, worker_env
from deep_reasoning.acp.runlog import Home
from deep_reasoning.acp.testing.fake_model import FakeOpenAI
from tests.acp.harness import dr_acp, run, scripted_env, write_config
from tests.acp.scenarios import repl, scripted

KEY = "sk-proxy-test-0123456789abcdef"
TOKEN = "token-proxy-test-0123456789abcdef"
MODEL = "metered-model"
# $0.001 per output token, input free: a call with max_tokens 10 reserves $0.01.
PRICES = PriceTable({MODEL: Price(0.0, 1000.0, None)})
CAP = 0.055  # room for five such calls


@dataclass
class Seen:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes


@dataclass
class Reply:
    status: int = 200
    content_type: str = "application/json"
    chunks: list[bytes] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


def completion(tokens_out: int = 10) -> bytes:
    usage = {"prompt_tokens": 3, "completion_tokens": tokens_out}
    return json.dumps({"id": "c", "choices": [], "usage": usage}).encode()


class Upstream:
    """A model provider on 127.0.0.1 that records each request and answers reply(seen)."""

    def __init__(self, reply: Callable[[Seen], Reply], latency_s: float = 0.0) -> None:
        self.seen: list[Seen] = []
        self._reply = reply
        self._latency_s = latency_s
        self._server: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    def __enter__(self) -> Self:
        upstream = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _any(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                seen = Seen(
                    self.command,
                    self.path,
                    {k.lower(): v for k, v in self.headers.items()},
                    self.rfile.read(length),
                )
                upstream.seen.append(seen)
                threading.Event().wait(upstream._latency_s)
                reply = upstream._reply(seen)
                body = b"".join(reply.chunks)
                self.send_response(reply.status)
                self.send_header("Content-Type", reply.content_type)
                self.send_header("Content-Length", str(len(body)))
                for name, value in reply.headers.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(body)

            do_POST = do_GET = _any

            def log_message(self, format: str, *args: Any) -> None:
                return None

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        self._server = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()


def answering(status: int = 200, body: bytes | None = None) -> Callable[[Seen], Reply]:
    return lambda seen: Reply(status, chunks=[completion() if body is None else body])


@pytest.fixture
def upstream() -> Iterator[Upstream]:
    with Upstream(answering()) as fake:
        yield fake


@pytest.fixture
def ledger(tmp_path: Path) -> SpendLedger:
    return SpendLedger(Home(tmp_path / "home"), CAP)


@pytest.fixture
def proxy(tmp_path: Path, ledger: SpendLedger) -> Iterator[KeyProxy]:
    proxy = KeyProxy(ledger=ledger, prices=PRICES, home=Home(tmp_path / "home"))
    yield proxy
    proxy.stop()


def call(
    proxy: KeyProxy,
    path: str,
    *,
    method: str = "POST",
    body: Any = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """One request to the proxy's ASGI app."""

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=proxy.app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://127.0.0.1:9"
        ) as client:
            return await client.request(
                method,
                path,
                content=None if body is None else json.dumps(body).encode(),
                headers={"Authorization": f"Bearer {TOKEN}", **(headers or {})},
            )

    return asyncio.run(send())


def chat(max_tokens: int = 10, **extra: Any) -> dict[str, Any]:
    return {"model": MODEL, "messages": [], "max_tokens": max_tokens, **extra}


def openai_route(proxy: KeyProxy, upstream: str, run: str = "run-1") -> str:
    route = proxy.add_route(
        session="s-1",
        run=run,
        dialect="openai",
        upstream=upstream,
        key=KEY,
        token=TOKEN,
    )
    return f"/r/{route.id}"


def test_the_token_is_swapped_for_the_key_and_the_call_forwarded(proxy, upstream):
    route = openai_route(proxy, upstream.url)
    response = call(proxy, f"{route}/chat/completions", body=chat())
    assert (response.status_code, response.content) == (200, completion())
    [seen] = upstream.seen
    assert (seen.method, seen.path) == ("POST", "/v1/chat/completions")
    assert seen.headers["authorization"] == f"Bearer {KEY}"
    assert json.loads(seen.body) == chat()
    assert TOKEN not in json.dumps(seen.headers)


def test_an_anthropic_route_swaps_the_x_api_key(proxy):
    message = {"type": "message", "usage": {"input_tokens": 1, "output_tokens": 1}}
    with Upstream(answering(body=json.dumps(message).encode())) as fake:
        route = proxy.add_route(
            session="s-1",
            run="run-1",
            dialect="anthropic",
            upstream=fake.url.removesuffix("/v1"),
            key=KEY,
            token=TOKEN,
        )
        response = call(
            proxy,
            f"/r/{route.id}/v1/messages",
            body=chat(),
            headers={"Authorization": "", "x-api-key": TOKEN},
        )
    assert response.status_code == 200
    [seen] = fake.seen
    assert (seen.path, seen.headers["x-api-key"]) == ("/v1/messages", KEY)
    assert "authorization" not in seen.headers


@pytest.mark.parametrize(
    "headers",
    [
        {"Authorization": ""},
        {"Authorization": "Bearer not-the-token"},
        {"Authorization": f"Bearer {KEY}"},
    ],
    ids=["missing", "wrong", "the-key-itself"],
)
def test_a_wrong_or_missing_token_is_refused_and_nothing_is_forwarded(
    proxy, upstream, headers
):
    route = openai_route(proxy, upstream.url)
    response = call(proxy, f"{route}/chat/completions", body=chat(), headers=headers)
    unknown = call(proxy, "/r/0123456789abcdef/chat/completions", body=chat())
    for refused in (response, unknown):
        assert refused.status_code == 401
        assert refused.json() == {
            "error": {
                "message": texts.BAD_TOKEN,
                "type": "bad_token",
                "code": "bad_token",
            }
        }
    assert upstream.seen == []


@pytest.mark.parametrize(
    ("method", "rest"),
    [
        ("POST", "files"),
        ("POST", "fine_tuning/jobs"),
        ("POST", "batches"),
        ("POST", "images/generations"),
        ("GET", "chat/completions"),
        ("POST", "chat/completions/../../files"),
    ],
)
def test_only_model_endpoints_are_forwarded(proxy, upstream, method, rest):
    route = openai_route(proxy, upstream.url)
    response = call(proxy, f"{route}/{rest}", method=method, body=chat())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_a_model_call"
    assert response.json()["error"]["message"].startswith(
        "The key proxy forwards only model calls (chat/completions, completions, "
        "embeddings); "
    )
    assert upstream.seen == []


def test_a_route_forwards_only_to_its_configured_upstream(proxy, upstream):
    with Upstream(answering()) as elsewhere:
        route = openai_route(proxy, upstream.url)
        other = elsewhere.url.removeprefix("http://")
        forwarded = call(
            proxy,
            f"{route}/chat/completions",
            body=chat(),
            headers={"Host": other, "X-Forwarded-Host": other},
        )
        smuggled = call(proxy, f"{route}//{other}/chat/completions", body=chat())
    assert (forwarded.status_code, smuggled.status_code) == (200, 403)
    assert len(upstream.seen) == 1
    assert elsewhere.seen == []
    assert other not in upstream.seen[0].headers.get("host", "")


def test_an_unpriced_model_is_refused_unless_the_upstream_is_loopback(
    tmp_path, proxy, upstream, ledger
):
    remote = openai_route(proxy, "https://models.example.invalid/v1", run="remote")
    refused = call(
        proxy, f"{remote}/chat/completions", body=chat(model="nobody-prices-this")
    )
    assert refused.status_code == 400
    assert refused.json()["error"]["message"] == texts.unpriced(
        "nobody-prices-this", str(tmp_path / "home")
    )
    local = openai_route(proxy, upstream.url, run="local")
    allowed = call(
        proxy, f"{local}/chat/completions", body=chat(model="nobody-prices-this")
    )
    assert allowed.status_code == 200
    assert len(upstream.seen) == 1
    assert ledger.spend("s-1").spent_usd == 0.0


def test_concurrent_calls_overshoot_the_cap_by_at_most_their_reservations(
    proxy, ledger
):
    with Upstream(answering(), latency_s=0.3) as slow:
        route = openai_route(proxy, slow.url)

        async def twenty() -> list[httpx.Response]:
            transport = httpx.ASGITransport(app=proxy.app())
            async with httpx.AsyncClient(
                transport=transport, base_url="http://127.0.0.1:9", timeout=30
            ) as client:
                return await asyncio.gather(
                    *(
                        client.post(
                            f"{route}/chat/completions",
                            content=json.dumps(chat()).encode(),
                            headers={"Authorization": f"Bearer {TOKEN}"},
                        )
                        for _ in range(20)
                    )
                )

        responses = asyncio.run(twenty())
    statuses = sorted(r.status_code for r in responses)
    assert statuses == [200] * 5 + [402] * 15
    spend = ledger.spend("s-1")
    assert (spend.calls, spend.refused, len(slow.seen)) == (5, 15, 5)
    assert spend.spent_usd == pytest.approx(0.05)
    assert spend.spent_usd <= CAP
    assert spend.reserved_usd == 0.0
    refusal = next(r for r in responses if r.status_code == 402)
    assert refusal.json()["error"]["code"] == "cap_reached"


def sse(*events: tuple[str | None, dict[str, Any] | str]) -> list[bytes]:
    chunks = []
    for name, data in events:
        head = f"event: {name}\n" if name else ""
        payload = data if isinstance(data, str) else json.dumps(data)
        chunks.append(f"{head}data: {payload}\n\n".encode())
    return chunks


def test_a_streamed_openai_call_is_metered_from_its_last_chunk(proxy, ledger):
    stream = sse(
        (None, {"choices": [{"delta": {"content": "a"}}]}),
        (None, {"choices": [], "usage": {"prompt_tokens": 7, "completion_tokens": 4}}),
        (None, "[DONE]"),
    )
    with Upstream(lambda seen: Reply(200, "text/event-stream", stream)) as fake:
        route = openai_route(proxy, fake.url)
        response = call(proxy, f"{route}/chat/completions", body=chat(stream=True))
    assert response.content == b"".join(stream)
    sent = json.loads(fake.seen[0].body)
    assert sent["stream_options"] == {"include_usage": True}
    assert ledger.spend("s-1").spent_usd == pytest.approx(0.004)


def test_a_streamed_anthropic_call_is_metered_from_message_start_and_delta(tmp_path):
    start = {"usage": {"input_tokens": 100, "cache_read_input_tokens": 50}}
    stream = sse(
        ("message_start", {"type": "message_start", "message": start}),
        ("content_block_delta", {"type": "content_block_delta", "delta": {}}),
        ("message_delta", {"type": "message_delta", "usage": {"output_tokens": 20}}),
        ("message_stop", {"type": "message_stop"}),
    )
    prices = PriceTable({MODEL: Price(1000.0, 1000.0, None)})
    ledger = SpendLedger(Home(tmp_path), 1.0)
    proxy = KeyProxy(ledger=ledger, prices=prices, home=Home(tmp_path))
    with Upstream(lambda seen: Reply(200, "text/event-stream", stream)) as fake:
        route = proxy.add_route(
            session="s-1",
            run="run-1",
            dialect="anthropic",
            upstream=fake.url,
            key=KEY,
            token=TOKEN,
        )
        response = call(
            proxy, f"/r/{route.id}/v1/messages", body=chat(max_tokens=50, stream=True)
        )
    assert response.content == b"".join(stream)
    assert ledger.spend("s-1").spent_usd == pytest.approx(170 * 0.001)


def test_upstream_error_bodies_never_echo_the_key(proxy):
    echo = json.dumps(
        {"error": {"message": f"Incorrect API key provided: {KEY}. Find yours..."}}
    ).encode()
    with Upstream(answering(401, echo)) as fake:
        route = openai_route(proxy, fake.url)
        response = call(proxy, f"{route}/chat/completions", body=chat())
    assert response.status_code == 401
    assert KEY not in response.text
    assert "Incorrect API key provided: [redacted]." in response.text


def test_provider_errors_release_their_reservations(proxy, ledger):
    """The OpenAI client retries a 500 four times: five reservations, which under a
    cap of five calls would leave no room for the next one if they stood."""
    overloaded = json.dumps({"error": {"message": "overloaded"}}).encode()

    def failing_five_times(seen: Seen) -> Reply:
        if len(fake.seen) <= 5:
            return Reply(500, chunks=[overloaded], headers={"retry-after-ms": "10"})
        return Reply(chunks=[completion()])

    with Upstream(failing_five_times) as fake:
        proxy.ensure_started()
        route = openai_route(proxy, fake.url)
        client = openai.OpenAI(
            base_url=f"{proxy.base_url}{route}", api_key=TOKEN, max_retries=4
        )
        with pytest.raises(openai.InternalServerError):
            client.chat.completions.create(**chat())
        after_errors = ledger.spend("s-1")
        client.chat.completions.create(**chat())
    assert len(fake.seen) == 6
    assert (after_errors.spent_usd, after_errors.reserved_usd, after_errors.calls) == (
        0.0,
        0.0,
        5,
    )
    assert ledger.spend("s-1").spent_usd == pytest.approx(0.01)


@pytest.mark.parametrize(
    ("status", "usage", "cost"),
    [
        (200, None, 0.01),  # no usage reported: the reservation stands
        (500, None, 0.0),  # a refusal that reports nothing cost nothing
        (400, {"prompt_tokens": 3, "completion_tokens": 4}, 0.004),
        (200, {"prompt_tokens": 3, "completion_tokens": 4}, 0.004),
    ],
    ids=["ok-silent", "error-silent", "error-with-usage", "ok-with-usage"],
)
def test_a_call_costs_its_reported_usage_else_its_reservation_unless_refused(
    proxy, ledger, status, usage, cost
):
    body = json.dumps({"id": "c", **({"usage": usage} if usage else {})}).encode()
    with Upstream(answering(status, body)) as fake:
        route = openai_route(proxy, fake.url)
        response = call(proxy, f"{route}/chat/completions", body=chat())
    assert response.status_code == status
    assert ledger.spend("s-1").spent_usd == pytest.approx(cost)
    assert ledger.spend("s-1").reserved_usd == 0.0


def test_a_released_runs_tokens_stop_working(proxy, upstream):
    route = openai_route(proxy, upstream.url, run="run-1")
    proxy.drop_run("run-1")
    response = call(proxy, f"{route}/chat/completions", body=chat())
    assert response.status_code == 401
    assert upstream.seen == []


def test_the_ledger_continues_after_a_restart(tmp_path):
    home = Home(tmp_path / "home")
    before = SpendLedger(home, 0.05)
    before.settle(before.reserve("s-1", 0.02), 0.03)
    after = SpendLedger(home, 0.05)
    assert after.reserve("s-1", 0.03) is None
    spend = after.spend("s-1")
    assert (spend.spent_usd, spend.calls, spend.refused) == (0.03, 1, 1)
    saved = json.loads((tmp_path / "home" / "spend" / "s-1.json").read_text())
    assert (saved["spent_usd"], saved["refused"]) == (0.03, 1)


def test_a_client_without_a_held_key_is_left_as_configured(proxy):
    route = ProxyRoute(proxy, {"PATH": "/bin", "OTHER_API_KEY": "x" * 20})
    grant = route.grant(
        session="s-1",
        run="run-1",
        upstream={"base_url": "http://127.0.0.1:8000/v1", "api_key_env": "LOCAL_KEY"},
    )
    assert grant == RouteGrant()


def granted(env: dict[str, str], proxy: KeyProxy, **upstreams: Any) -> RouteGrant:
    return ProxyRoute(proxy, env).grant(
        session="s-1",
        run="run-1",
        upstream={"base_url": "https://api.example.invalid/v1", "api_key_env": "K"},
        **upstreams,
    )


def test_the_key_is_removed_from_the_worker_env_by_value_under_any_name(proxy):
    secret = "oh-secret-0123456789abcdef"
    env = {
        "PATH": "/usr/bin:/bin",
        "K": KEY,
        "MY_KEY_COPY": KEY,
        "IN_A_URL": f"https://user:{KEY}@example.invalid",
        "OH_SECRET_KEY": secret,
        "SECRET_COPY": secret,
        "SESSION_API_KEY": "bin",  # short: its value must not remove PATH
        "ANTHROPIC_API_KEY": "sk-ant-0123456789abcdef",
    }
    grant = granted(env, proxy)
    worker = worker_env(env, grant)
    assert worker["PATH"] == "/usr/bin:/bin"
    assert {"MY_KEY_COPY", "IN_A_URL", "SECRET_COPY", "OH_SECRET_KEY"}.isdisjoint(
        worker
    )
    assert worker["K"] not in env.values()
    assert worker["ANTHROPIC_API_KEY"] not in env.values()
    assert worker["ANTHROPIC_BASE_URL"].startswith(proxy.base_url + "/r/")
    for value in (KEY, secret, env["ANTHROPIC_API_KEY"]):
        assert not [k for k, v in worker.items() if value in v]
    assert grant.client_overrides == {
        "base_url": grant.client_overrides["base_url"],
        "api_key_env": "K",
    }
    assert grant.client_overrides["base_url"].startswith(proxy.base_url + "/r/")


def test_a_tool_with_its_own_client_gets_its_own_overrides(proxy, upstream):
    env = {"OPENAI_API_KEY": KEY}
    grant = granted(
        env,
        proxy,
        tool_upstreams={
            "rag": {"base_url": upstream.url, "api_key_env": "OPENAI_API_KEY"},
            "local": {"base_url": "http://127.0.0.1:1/v1", "api_key_env": "NONE"},
        },
    )
    # NONE is unset, so like the main client's K it falls back to OPENAI_API_KEY,
    # as deep_reasoner's build_client does.
    assert set(grant.tool_client_overrides) == {"rag", "local"}
    assert grant.tool_client_overrides["rag"]["api_key_env"] == "OPENAI_API_KEY"
    assert grant.client_overrides["api_key_env"] == "OPENAI_API_KEY"
    assert grant.env_add["OPENAI_API_KEY"] != KEY
    assert (
        len(
            {
                grant.client_overrides["base_url"],
                *(o["base_url"] for o in grant.tool_client_overrides.values()),
            }
        )
        == 3
    )


@pytest.mark.parametrize(
    ("env", "system", "proxies", "expected"),
    [
        (
            {},
            "Darwin",
            {"http": "http://corp:3128", "https": "http://corp:3129"},
            {
                "NO_PROXY": "127.0.0.1,localhost,::1",
                "HTTP_PROXY": "http://corp:3128",
                "HTTPS_PROXY": "http://corp:3129",
            },
        ),
        (
            {"NO_PROXY": "internal.example"},
            "Linux",
            {"http": "http://corp:3128"},
            {"NO_PROXY": "internal.example,127.0.0.1,localhost,::1"},
        ),
        (
            {"HTTPS_PROXY": "http://mine:8080"},
            "Darwin",
            {"https": "http://corp:3129"},
            {"NO_PROXY": "127.0.0.1,localhost,::1"},
        ),
    ],
    ids=["macos-system-proxies", "linux", "environment-proxy-wins"],
)
def test_loopback_calls_bypass_macos_system_proxies_and_others_keep_them(
    env, system, proxies, expected
):
    assert loopback_proxy_env(env, system=system, system_proxies=lambda: proxies) == (
        expected
    )


def test_the_proxy_never_logs_a_key_or_a_token(tmp_path, ledger, capfd, caplog):
    caplog.set_level(logging.DEBUG)
    proxy = KeyProxy(ledger=ledger, prices=PRICES, home=Home(tmp_path / "home"))
    try:
        with Upstream(answering()) as fake:
            env = {"OPENAI_API_KEY": KEY}
            grant = ProxyRoute(proxy, env).grant(
                session="s-1",
                run="run-1",
                upstream={"base_url": fake.url, "api_key_env": "OPENAI_API_KEY"},
            )
            token = grant.env_add["OPENAI_API_KEY"]
            base = grant.client_overrides["base_url"]
            auth = {"Authorization": f"Bearer {token}"}
            with httpx.Client(trust_env=False) as client:
                statuses = [
                    client.post(f"{base}/chat/completions", json=chat(), headers=auth)
                    for _ in range(7)
                ]
                statuses.append(client.post(f"{base}/files", json={}, headers=auth))
                statuses.append(client.post(f"{base}/chat/completions", json=chat()))
    finally:
        proxy.stop()
    assert [r.status_code for r in statuses] == [200] * 5 + [402] * 2 + [403, 401]
    captured = capfd.readouterr()
    logged = captured.out + captured.err + caplog.text
    assert "refused" in logged
    assert KEY not in logged
    assert token not in logged


@pytest.mark.parametrize(
    ("args", "worker_sees_the_key"),
    [((), False), (("--no-key-proxy",), True)],
    ids=["proxied", "no-key-proxy"],
)
def test_no_key_proxy_keeps_d1s_direct_route(
    tmp_path, home, work, args, worker_sees_the_key
):
    key = "sk-direct-0123456789abcdef"
    plan = {
        "Which key?": [
            repl(
                "import os", "print(os.environ['OPENAI_API_KEY'] == " + repr(key) + ")"
            ),
            repl("FinalAnswer('checked')"),
        ]
    }

    async def body():
        async with FakeOpenAI(scripted(plan)) as model:
            config = write_config(
                tmp_path / "config" / "main.yaml",
                {
                    "model": "fake-model",
                    "client": {
                        "base_url": model.base_url,
                        "api_key_env": "OPENAI_API_KEY",
                        "max_retries": 0,
                    },
                    "system_prompt": "s",
                    "max_iter": 4,
                },
            )
            env = scripted_env(OPENAI_API_KEY=key)
            async with dr_acp(config, home, args=args, env=env) as client:
                root = await client.open_session(work)
                await client.ask(root, "Which key?")
                outputs = [
                    u.get("rawOutput")
                    for u in client.updates_on(root)
                    if u["sessionUpdate"] == "tool_call_update"
                ]
        return outputs, model.calls

    outputs, calls = run(body())
    assert str(worker_sees_the_key) in outputs
    assert {c.authorization for c in calls} == {f"Bearer {key}"}
