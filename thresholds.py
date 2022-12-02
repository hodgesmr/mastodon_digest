from enum import Enum

from scipy import stats

from models import ScoredPost
from scorers import Scorer


class Threshold(Enum):
    LAX = 90
    NORMAL = 95
    STRICT = 98

    def posts_meeting_criteria(
        self, posts: list[ScoredPost], scorer: Scorer
    ) -> list[ScoredPost]:
        all_post_scores = [p.get_score(scorer) for p in posts]
        threshold_posts = [
            p
            for p in posts
            if stats.percentileofscore(all_post_scores, p.get_score(scorer))
            > self.value
        ]

        return threshold_posts


def get_thresholds():
    return {i.name.lower(): i.value for i in Threshold}


def get_threshold_from_name(name: str) -> Threshold:
    return Threshold[name.upper()]
