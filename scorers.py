from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import TYPE_CHECKING

from scipy import stats

if TYPE_CHECKING:
    from models import ScoredPost


class Weight(ABC):
    @classmethod
    @abstractmethod
    def weight(cls, scored_post: ScoredPost):
        pass


class UniformWeight(Weight):
    @classmethod
    def weight(cls, scored_post: ScoredPost):
        return 1


class InverseFollowerWeight(Weight):
    @classmethod
    def weight(cls, scored_post: ScoredPost):
        # Zero out posts by accounts with zero followers that somehow made it to my feed
        if scored_post.info["account"]["followers_count"] == 0:
            weight = 0
        else:
            # inversely weight against how big the account is
            weight = 1 / sqrt(scored_post.info["account"]["followers_count"])

        return weight


class Scorer(ABC):
    @classmethod
    @abstractmethod
    def score(cls, scored_post: ScoredPost):
        pass


class SimpleScorer(Scorer, UniformWeight):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        metric_average = stats.gmean(
            [
                scored_post.info["reblogs_count"],
                scored_post.info["favourites_count"],
            ]
        )
        return metric_average * super().weight(scored_post)


class SimpleWeightedScorer(SimpleScorer, InverseFollowerWeight):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        return super().score(scored_post) * super().weight(scored_post)


class ExtendedSimpleScorer(Scorer, UniformWeight):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        metric_average = stats.gmean(
            [
                scored_post.info["reblogs_count"],
                scored_post.info["favourites_count"],
                scored_post.info["replies_count"],
            ],
        )
        return metric_average * super().weight(scored_post)


class ExtendedSimpleWeightedScorer(ExtendedSimpleScorer, InverseFollowerWeight):
    @classmethod
    def score(cls, scored_post: ScoredPost):
        return super().score(scored_post) * super().weight(scored_post)
