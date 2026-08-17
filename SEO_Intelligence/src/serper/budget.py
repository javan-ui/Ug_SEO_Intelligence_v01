from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class SearchBudgetManager:
    total: int
    attempted: int = 0
    successful: int = 0
    failed: int = 0
    cached: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.total - self.attempted)

    def can_search(self) -> bool:
        return self.remaining > 0

    def record_attempt(self) -> None:
        if not self.can_search():
            raise RuntimeError("Serper search budget exhausted.")
        self.attempted += 1

    def record_success(self) -> None:
        self.successful += 1

    def record_failure(self) -> None:
        self.failed += 1

    def record_cached(self) -> None:
        self.cached += 1

    def to_dict(self) -> dict[str, int]:
        return {**asdict(self), "remaining": self.remaining}