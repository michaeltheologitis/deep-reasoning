"""Prices per model, and what a call or a session has cost (§4.7, §6.2)."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from deep_reasoning.acp.runlog import Home

CostSource = Literal["provider", "table", "claude"]


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


class PriceTable:
    def __init__(self, prices: Mapping[str, Price]) -> None: ...

    @classmethod
    def load(cls, home: "Home") -> "PriceTable":
        """The package's prices.yaml, with $DR_HOME/prices.yaml over it."""
        raise NotImplementedError

    def estimate(self, model: str | None, usage: Mapping[str, Any]) -> CostEstimate:
        """usage["cost"] when the provider reports it (source provider); else the entry
        whose key equals the model id, or the longest matching glob (source table);
        else usd None."""
        raise NotImplementedError
