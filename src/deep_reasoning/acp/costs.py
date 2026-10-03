"""Prices per model, and what a call or a session has cost (§4.7, §6.2)."""

import fnmatch
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import yaml
from genai_prices import Usage
from genai_prices.data import providers
from genai_prices.data_snapshot import DataSnapshot

if TYPE_CHECKING:
    from deep_reasoning.acp.runlog import Home

CostSource = Literal["provider", "table", "claude"]
MILLION = 1_000_000
# genai-prices' bundled data, never a download: calc_price reads the process-wide
# snapshot, which UpdatePrices replaces with what it fetches.
GENAI_PRICES = DataSnapshot(providers=providers, from_auto_update=False)


@dataclass(frozen=True)
class CostLedger:
    usd: float = 0.0
    complete: bool = True  # False once any contributing call had no cost estimate
    tokens_in: int = 0
    tokens_out: int = 0


NO_COST = CostLedger()


@dataclass(frozen=True)
class Price:
    input_per_mtok: float
    output_per_mtok: float
    context_window: int | None


@dataclass(frozen=True)
class CostEstimate:
    usd: float | None
    source: CostSource | None
    tokens_in: int
    tokens_out: int
    context_window: int | None


def _prices(raw: Mapping[str, Any] | None) -> dict[str, Price]:
    return {
        model: Price(
            input_per_mtok=float(entry["input_per_mtok"]),
            output_per_mtok=float(entry["output_per_mtok"]),
            context_window=entry.get("context_window"),
        )
        for model, entry in (raw or {}).items()
    }


class PriceTable:
    """The home's own entries, laid over genai-prices."""

    def __init__(self, prices: Mapping[str, Price]) -> None:
        self._prices = dict(prices)

    @classmethod
    def load(cls, home: "Home") -> "PriceTable":
        """$DR_HOME/prices.yaml: per model id or glob, input_per_mtok and
        output_per_mtok in USD per million tokens, and context_window in tokens."""
        override = home.root / "prices.yaml"
        raw = yaml.safe_load(override.read_text()) if override.exists() else None
        return cls(_prices(raw))

    def price(self, model: str | None) -> Price | None:
        """The entry whose key is the model id, else the longest glob that matches it."""
        if model is None:
            return None
        if model in self._prices:
            return self._prices[model]
        globs = [key for key in self._prices if fnmatch.fnmatchcase(model, key)]
        return self._prices[max(globs, key=len)] if globs else None

    def estimate(self, model: str | None, usage: Mapping[str, Any]) -> CostEstimate:
        """The provider's reported cost when it gives one; else the table's price; else
        usd None: an unknown cost, never zero."""
        tokens_in = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        tokens_out = int(
            usage.get("completion_tokens") or usage.get("output_tokens") or 0
        )
        usd, window = self._table(model, tokens_in, tokens_out)
        if usage.get("cost") is not None:
            return CostEstimate(
                float(usage["cost"]), "provider", tokens_in, tokens_out, window
            )
        source = "table" if usd is not None else None
        return CostEstimate(usd, source, tokens_in, tokens_out, window)

    def _table(
        self, model: str | None, tokens_in: int, tokens_out: int
    ) -> tuple[float | None, int | None]:
        """USD and context window from the home's entry, else from genai-prices;
        (None, None) for a model neither knows."""
        if price := self.price(model):
            usd = tokens_in * price.input_per_mtok + tokens_out * price.output_per_mtok
            return usd / MILLION, price.context_window
        if model is None:
            return None, None
        usage = Usage(input_tokens=tokens_in, output_tokens=tokens_out)
        try:
            priced = GENAI_PRICES.calc(usage, model, None, None, None)
        except LookupError:
            return None, None
        return float(priced.total_price), priced.model.context_window
