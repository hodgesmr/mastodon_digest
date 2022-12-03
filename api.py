from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from models import ScoredPost

if TYPE_CHECKING:
    from mastodon import Mastodon


def fetch_posts_and_boosts(
    hours: int, mastodon_client: Mastodon, mastodon_username: str
) -> tuple[list[ScoredPost], list[ScoredPost]]:
    """Fetches posts form the home timeline that the account hasn't interactied with"""

    TIMELINE_LIMIT = 1000

    # First, get our filters
    filters = mastodon_client.filters()

    # Set our start query
    start = datetime.now(timezone.utc) - timedelta(hours=hours)

    posts = []
    boosts = []
    seen_post_urls = set()
    total_posts_seen = 0

    # Iterate over our home timeline until we run out of posts or we hit the limit
    response = mastodon_client.timeline(min_id=start)
    while response and total_posts_seen < TIMELINE_LIMIT:

        # Apply our server-side filters
        if filters:
            filtered_response = mastodon_client.filters_apply(response, filters, "home")
        else:
            filtered_response = response

        for post in filtered_response:
            total_posts_seen += 1

            boost = False
            if post["reblog"] is not None:
                post = post["reblog"]  # look at the bosted post
                boost = True

            scored_post = ScoredPost(post)  # wrap the post data as a ScoredPost

            if scored_post.url not in seen_post_urls:
                # Apply our local filters
                # Basically ignore my posts or posts I've interacted with
                if (
                    not scored_post.info["reblogged"]
                    and not scored_post.info["favourited"]
                    and not scored_post.info["bookmarked"]
                    and scored_post.info["account"]["acct"] != mastodon_username
                ):
                    # Append to either the boosts list or the posts lists
                    if boost:
                        boosts.append(scored_post)
                    else:
                        posts.append(scored_post)
                    seen_post_urls.add(scored_post.url)

        response = mastodon_client.fetch_previous(
            response
        )  # fext the previous (because of reverse chron) page of results

    return posts, boosts
