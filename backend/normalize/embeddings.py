from typing import Protocol


class EmbeddingSimilarity(Protocol):
    def score(self, left: str, right: str) -> float:
        ...


class NoOpEmbeddingSimilarity:
    def score(self, left: str, right: str) -> float:
        return 0.0
