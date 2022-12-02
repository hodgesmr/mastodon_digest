from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import TYPE_CHECKING

from scipy import stats

if TYPE_CHECKING:
    from models import ScoredPost


class Scorer(ABC):
    @classmethod
    @abstractmethod
    def score(cls, scored_post: ScoredPost):
        pass


class SimpleScorer(Scorer):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        metric_average = stats.gmean(
            [scored_post.info["reblogs_count"], scored_post.info["favourites_count"]]
        )
        return metric_average


class SimpleWeightedScorer(SimpleScorer):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        unweighted_score = super().score(scored_post)
        weight = 1 / sqrt(scored_post.info["account"]["followers_count"])

        return unweighted_score * weight
