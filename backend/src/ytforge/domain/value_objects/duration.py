from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Duration:
    seconds: Decimal

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("Duration must be positive")
