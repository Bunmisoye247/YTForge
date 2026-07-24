from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrendScore:
    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            raise ValueError("TrendScore must be between 0 and 100")
