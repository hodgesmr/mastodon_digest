from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib3.util.url import parse_url
from typing import TYPE_CHECKING

from models import ScoredPost

if TYPE_CHECKING:
    from mastodon import Mastodon

# Toggle debugging output
VERB = False

def get_full_account_name(acct : str, default_host : str) -> str:
    """
    Adds the default hostname to the user name if not present
    """
    if acct == "":
        return ""
    if len(acct.split("@")) == 2:
        return acct
    else:
        return "@".join((acct, default_host))
    
            
def getOriginalPost(post):
    """
    Uses flipton to fetch post information from the home instance of a single post
    """
    from flipton.flipton import MastodonInstanceSwitcher, FliptonError
    post_id = post.url.split("/")[-1]
    if not post_id.isdecimal():
        return None
    home_instance = parse_url(post.url).hostname
    mst = MastodonInstanceSwitcher()
    try:
        original_post = mst.status(host=home_instance, id=post_id)
    except FliptonError:
        original_post = None
    return original_post


def update_posts_with_flipton(posts, boosts, timeout_secs = 30):
    """ 
    Fetch in parallel the original posts corresponding the given posts 
    and boosts, which were obtained from the user's home instance.
    """
    import time
    from multiprocessing import Pool, cpu_count
    if VERB:
        print("Retrieving original posts for %d items. (Timeout after %d seconds.)"%(len(posts)+len(boosts), timeout_secs))
    p = Pool(processes=min(10, cpu_count()))
    res = [p.apply_async(getOriginalPost, args=(post,)) for post in posts+boosts]
    t0 = datetime.now()
    busy = True
    while (datetime.now()-t0).seconds < timeout_secs and busy:
        busy = False
        for r in res:
            if not r.ready():
                busy = True
                break
        if busy:
            time.sleep(1)
    nSuccess = 0
    for i, r in enumerate(res):
        if not r.ready() or not r.successful():
            continue
        original_post = r.get()
        if original_post is None:
            continue
        original_post = ScoredPost(original_post)
        nSuccess+=1
        if i < len(posts):
            posts[i] = original_post
        else:
            boosts[i-len(posts)] = original_post
    if VERB:
        print("Successfully retrieved: %d/%d (timed out: %s)"%(nSuccess, len(posts)+len(boosts), busy))
    p.terminate()
    p.join()


def fetch_posts_and_boosts(
    hours: int, mastodon_client: Mastodon, timeline: str, use_flipton: bool
) -> tuple[list[ScoredPost], list[ScoredPost]]:
    """Fetches posts from the home timeline that the account hasn't interacted with"""

    TIMELINE_LIMIT = 1000  # Should this be documented? Configurable?

    # First, get our filters
    filters = mastodon_client.filters()

    # Set our start query
    start = datetime.now(timezone.utc) - timedelta(hours=hours)

    posts = []
    boosts = []
    seen_post_urls = set()
    total_posts_seen = 0

    # If timeline name is specified as hashtag:tagName or list:list-name, look-up with those names,
    # else accept 'federated' and 'local' to process from the server public and local timelines.
    #
    # We default to 'home' if the name is unrecognized
    if ":" in timeline:
        timelineType, timelineId = timeline.lower().split(":", 1)
    else:
        timelineType = timeline.lower()

    if timelineType == "hashtag":
        response = mastodon_client.timeline_hashtag(timelineId, min_id=start)
    elif timelineType == "list":
        if not timelineId.isnumeric():
            raise TypeError('Cannot load list timeline: ID must be numeric, e.g.: https://example.social/lists/4 would be list:4')

        response = mastodon_client.timeline_list(timelineId, min_id=start)
    elif timelineType == "federated":
        response = mastodon_client.timeline_public(min_id=start)
    elif timelineType == "local":
        response = mastodon_client.timeline_local(min_id=start)
    else:
        response = mastodon_client.timeline(min_id=start)

    mastodon_acct = mastodon_client.me()['acct'].strip().lower()

    # Iterate over our timeline until we run out of posts or we hit the limit
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
                post = post["reblog"]  # look at the boosted post
                boost = True

            scored_post = ScoredPost(post)  # wrap the post data as a ScoredPost

            if scored_post.url not in seen_post_urls:
                # Apply our local filters
                # Basically ignore my posts or posts I've interacted with
                # and ignore posts from accounts that have "#noindex" or "#nobot"
                if (
                    not scored_post.info["reblogged"]
                    and not scored_post.info["favourited"]
                    and not scored_post.info["bookmarked"]
                    and scored_post.info["account"]["acct"].strip().lower() != mastodon_acct
                    and "#noindex" not in scored_post.info["account"]["note"].lower()
                    and "#nobot" not in scored_post.info["account"]["note"].lower()
                ):
                    # Append to either the boosts list or the posts lists
                    if boost:
                        boosts.append(scored_post)
                    else:
                        posts.append(scored_post)
                    seen_post_urls.add(scored_post.url)

        response = mastodon_client.fetch_previous(
            response
        )  # fetch the previous (because of reverse chron) page of results

    if use_flipton:
        update_posts_with_flipton(posts, boosts)

    return posts, boosts
