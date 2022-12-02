from math import sqrt

from scipy import stats


class ScoredPost:
    def __init__(self, info: dict):
        self.info = info

    @property
    def url(self) -> str:
        return self.info["url"]

    def get_home_url(self, mastodon_base_url: str) -> str:
        return f"{mastodon_base_url}/authorize_interaction?uri={self.url}"

    @property
    def score(self) -> float:
        # geometric mean of boosts and favs
        metric_average = stats.gmean(
            [self.info["reblogs_count"], self.info["favourites_count"]]
        )

        # Zero out posts by accounts with zero followers that somehow made it to my feed
        if self.info["account"]["followers_count"] == 0:
            weight = 0
        else:
            # inversely weight against how big the account is
            weight = 1 / sqrt(self.info["account"]["followers_count"])

        return metric_average * weight
