from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def __add__(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise ValueError(f"Cannot add {other.currency} to {self.currency}")
        return Money(self.amount + other.amount, self.currency)
