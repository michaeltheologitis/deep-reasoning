import pytest
import yaml

from deep_reasoning.acp.costs import CostEstimate, Price, PriceTable
from deep_reasoning.acp.runlog import Home

TABLE = PriceTable(
    {
        "gpt-6-luna": Price(
            input_per_mtok=0.1, output_per_mtok=0.5, context_window=1_050_000
        ),
        "openai/*": Price(input_per_mtok=1.0, output_per_mtok=1.0, context_window=None),
        "openai/gpt-*": Price(
            input_per_mtok=2.0, output_per_mtok=4.0, context_window=8
        ),
    }
)


def test_a_table_price_is_per_million_tokens_in_and_out():
    usage = {"prompt_tokens": 1_000_000, "completion_tokens": 2_000_000}
    assert TABLE.estimate("gpt-6-luna", usage) == CostEstimate(
        usd=pytest.approx(1.1),
        source="table",
        tokens_in=1_000_000,
        tokens_out=2_000_000,
        context_window=1_050_000,
    )


def test_the_longest_matching_glob_prices_a_model_without_an_exact_entry():
    estimate = TABLE.estimate(
        "openai/gpt-x", {"input_tokens": 1_000_000, "output_tokens": 0}
    )
    assert (estimate.usd, estimate.context_window) == (pytest.approx(2.0), 8)


def test_a_provider_reported_cost_wins_over_the_table():
    estimate = TABLE.estimate(
        "gpt-6-luna", {"prompt_tokens": 10, "completion_tokens": 1, "cost": 0.5}
    )
    assert (estimate.usd, estimate.source) == (0.5, "provider")


def test_an_unknown_model_has_an_unknown_cost_not_zero():
    estimate = TABLE.estimate("mystery", {"prompt_tokens": 10, "completion_tokens": 1})
    assert estimate == CostEstimate(
        usd=None, source=None, tokens_in=10, tokens_out=1, context_window=None
    )


def test_the_shipped_table_prices_gpt_6_luna_and_home_overrides_it(tmp_path):
    shipped = PriceTable.load(Home(tmp_path))
    assert (
        shipped.estimate("gpt-6-luna", {"prompt_tokens": 1, "completion_tokens": 1}).usd
        is not None
    )
    (tmp_path / "prices.yaml").write_text(
        yaml.safe_dump(
            {
                "gpt-6-luna": {
                    "input_per_mtok": 1,
                    "output_per_mtok": 1,
                    "context_window": 5,
                }
            }
        )
    )
    overridden = PriceTable.load(Home(tmp_path))
    assert (
        overridden.estimate(
            "gpt-6-luna", {"prompt_tokens": 1_000_000, "completion_tokens": 0}
        ).usd
        == 1
    )
