import subprocess
import sys

import genai_prices
import pytest
import yaml
from genai_prices import data_snapshot

from deep_reasoning.acp.costs import CostEstimate, Price, PriceTable
from deep_reasoning.acp.runlog import Home

GENAI_PRICES = PriceTable({})
HOME_GLOBS = PriceTable(
    {
        "openai/*": Price(input_per_mtok=1.0, output_per_mtok=1.0, context_window=None),
        "openai/gpt-*": Price(
            input_per_mtok=2.0, output_per_mtok=4.0, context_window=8
        ),
    }
)
LUNA_WINDOW = 1_050_000
SHORT_PROMPT = {"prompt_tokens": 100_000, "completion_tokens": 10_000}
LONG_PROMPT = {"prompt_tokens": 300_000, "completion_tokens": 10_000}
# Prices a call in a fresh interpreter that cannot resolve a host or open a connection.
OFFLINE = """
import socket, sys, threading

def refuse(*args, **kwargs):
    raise OSError("this test has no network")

socket.getaddrinfo = refuse
socket.socket.connect = refuse

from pathlib import Path
from deep_reasoning.acp.costs import PriceTable
from deep_reasoning.acp.runlog import Home

usage = {"prompt_tokens": 300_000, "completion_tokens": 10_000}
print(PriceTable.load(Home(Path(sys.argv[1]))).estimate("gpt-6-luna", usage).usd)
print(threading.active_count())
"""


@pytest.mark.parametrize(
    ("tokens_in", "tokens_out", "usd"),
    [
        (100_000, 10_000, 0.0150),  # $0.10 in and $0.50 out per million tokens
        (272_000, 0, 0.0272),
        (272_001, 0, 0.0544002),  # above 272K input tokens: $0.20 in, $0.75 out
        (300_000, 10_000, 0.0675),
        (1_000_000, 2_000_000, 1.7),
    ],
)
def test_genai_prices_prices_gpt_6_luna_and_a_prompt_above_272k_tokens_at_its_long_rates(
    tokens_in, tokens_out, usd
):
    usage = {"prompt_tokens": tokens_in, "completion_tokens": tokens_out}
    assert GENAI_PRICES.estimate("gpt-6-luna", usage) == CostEstimate(
        usd=usd,
        source="table",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        context_window=LUNA_WINDOW,
    )


@pytest.mark.parametrize("model", ["mystery", None])
def test_a_model_genai_prices_does_not_know_has_an_unknown_cost_not_zero(model):
    estimate = GENAI_PRICES.estimate(model, {"input_tokens": 10, "output_tokens": 1})
    assert estimate == CostEstimate(
        usd=None, source=None, tokens_in=10, tokens_out=1, context_window=None
    )


def test_a_provider_reported_cost_wins_over_genai_prices():
    estimate = GENAI_PRICES.estimate("gpt-6-luna", {**SHORT_PROMPT, "cost": 0.5})
    assert (estimate.usd, estimate.source, estimate.context_window) == (
        0.5,
        "provider",
        LUNA_WINDOW,
    )


def test_the_longest_matching_home_glob_prices_a_model_without_an_exact_entry():
    estimate = HOME_GLOBS.estimate(
        "openai/gpt-x", {"input_tokens": 1_000_000, "output_tokens": 0}
    )
    assert (estimate.usd, estimate.context_window) == (pytest.approx(2.0), 8)


def test_a_home_entry_overrides_genai_prices_and_prices_a_model_it_does_not_know(
    tmp_path,
):
    luna = PriceTable.load(Home(tmp_path)).estimate("gpt-6-luna", LONG_PROMPT)
    assert luna.usd == 0.0675
    (tmp_path / "prices.yaml").write_text(
        yaml.safe_dump(
            {
                "gpt-6-luna": {
                    "input_per_mtok": 1,
                    "output_per_mtok": 1,
                    "context_window": 5,
                },
                "fake-model": {"input_per_mtok": 1, "output_per_mtok": 2},
            }
        )
    )
    home = PriceTable.load(Home(tmp_path))
    luna = home.estimate("gpt-6-luna", LONG_PROMPT)
    assert (luna.usd, luna.source, luna.context_window) == (
        pytest.approx(0.31),
        "table",
        5,
    )
    assert home.estimate("fake-model", LONG_PROMPT).usd == pytest.approx(0.32)


@pytest.fixture
def fetched_prices():
    """What UpdatePrices, genai-prices' opt-in download, leaves behind: the snapshot that
    calc_price reads, swapped process-wide; this one knows no model."""
    data_snapshot.set_custom_snapshot(
        data_snapshot.DataSnapshot(providers=[], from_auto_update=True)
    )
    yield
    data_snapshot.set_custom_snapshot(None)


def test_prices_come_from_genai_prices_bundled_data_even_after_a_download(
    fetched_prices,
):
    with pytest.raises(LookupError):
        genai_prices.calc_price(genai_prices.Usage(input_tokens=1), "gpt-6-luna")
    assert GENAI_PRICES.estimate("gpt-6-luna", SHORT_PROMPT).usd == 0.0150


def test_pricing_a_call_needs_no_network_and_starts_no_background_thread(tmp_path):
    result = subprocess.run(
        [sys.executable, "-c", OFFLINE, str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.split() == ["0.0675", "1"]
