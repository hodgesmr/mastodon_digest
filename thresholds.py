from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from scipy import stats

if TYPE_CHECKING:
    from models import ScoredPost
    from scorers import Scorer


class Threshold(Enum):
    LAX = 90
    NORMAL = 95
    STRICT = 98

    def get_name(self):
        return self.name.lower()

    def posts_meeting_criteria(
        self, posts: list[ScoredPost], scorer: Scorer
    ) -> list[ScoredPost]:
        """Returns a list of ScoredPosts that meet this Threshold with the given Scorer"""

        all_post_scores = [p.get_score(scorer) for p in posts]
        threshold_posts = [
            p
            for p in posts
            if stats.percentileofscore(all_post_scores, p.get_score(scorer))
            >= self.value
        ]

        return threshold_posts


def get_thresholds():
    """Returns a dictionary mapping lowercase threshold names to values"""

    return {i.get_name(): i.value for i in Threshold}


def get_threshold_from_name(name: str) -> Threshold:
    """Returns Threshold for a given named string"""

    return Threshold[name.upper()]
