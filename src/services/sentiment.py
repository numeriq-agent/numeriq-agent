from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SentimentModel(Protocol):
    def score(self, text: str) -> float:
        ...


@dataclass
class RuleBasedSentiment(SentimentModel):
    positive_keywords: tuple[str, ...] = ("beat", "outperform", "growth", "surge")
    negative_keywords: tuple[str, ...] = ("miss", "downgrade", "loss", "fall")

    def score(self, text: str) -> float:
        text_lower = text.lower()
        pos_hits = sum(kw in text_lower for kw in self.positive_keywords)
        neg_hits = sum(kw in text_lower for kw in self.negative_keywords)
        if pos_hits == neg_hits == 0:
            return 0.0
        return (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)
