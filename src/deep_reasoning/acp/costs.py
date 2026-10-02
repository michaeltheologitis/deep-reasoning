"""Prices per model, and what a call or a session has cost (§4.7, §6.2)."""

import fnmatch
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from typing import TYPE_CHECKING, Any, Literal

import yaml

if TYPE_CHECKING:
    from deep_reasoning.acp.runlog import Home

CostSource = Literal["provider", "table", "claude"]
MILLION = 1_000_000


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
    def __init__(self, prices: Mapping[str, Price]) -> None:
        self._prices = dict(prices)

    @classmethod
    def load(cls, home: "Home") -> "PriceTable":
        """The package's prices.yaml, with $DR_HOME/prices.yaml over it."""
        shipped = files("deep_reasoning.acp").joinpath("prices.yaml").read_text()
        prices = _prices(yaml.safe_load(shipped))
        override = home.root / "prices.yaml"
        if override.exists():
            prices |= _prices(yaml.safe_load(override.read_text()))
        return cls(prices)

    def price(self, model: str | None) -> Price | None:
        """The entry whose key is the model id, else the longest glob that matches it."""
        if model is None:
            return None
        if model in self._prices:
            return self._prices[model]
        globs = [key for key in self._prices if fnmatch.fnmatchcase(model, key)]
        return self._prices[max(globs, key=len)] if globs else None

    def estimate(self, model: str | None, usage: Mapping[str, Any]) -> CostEstimate:
        """usage["cost"] when the provider reports it (source provider); else the entry
        whose key equals the model id, or the longest matching glob (source table);
        else usd None."""
        tokens_in = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        tokens_out = int(
            usage.get("completion_tokens") or usage.get("output_tokens") or 0
        )
        price = self.price(model)
        window = price.context_window if price else None
        if usage.get("cost") is not None:
            return CostEstimate(
                float(usage["cost"]), "provider", tokens_in, tokens_out, window
            )
        if price is None:
            return CostEstimate(None, None, tokens_in, tokens_out, None)
        usd = (
            tokens_in * price.input_per_mtok + tokens_out * price.output_per_mtok
        ) / MILLION
        return CostEstimate(usd, "table", tokens_in, tokens_out, window)
