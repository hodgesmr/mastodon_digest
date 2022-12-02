import argparse
import os
import sys
import tempfile
import webbrowser
from datetime import datetime, timedelta, timezone

from jinja2 import Environment, FileSystemLoader
from mastodon import Mastodon
from scipy import stats

from models import ScoredPost
from scorers import Scorer, get_scorers
from thresholds import Threshold, get_thresholds, get_threshold_from_name


def fetch_posts_and_boosts(
    hours: int, mastodon_client: Mastodon, mastodon_username: str
) -> tuple[list[ScoredPost], list[ScoredPost]]:
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
        filtered_response = mastodon_client.filters_apply(response, filters, "home")

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


def render_and_open_digest(context: dict) -> None:
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("digest.html.jinja")
    output_html = template.render(context)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as out_file:
        final_url = f"file://{out_file.name}"
        out_file.write(output_html)

    webbrowser.open(final_url)


def run(
    hours: int,
    scorer: Scorer,
    threshold: Threshold,
    mastodon_token: str,
    mastodon_base_url: str,
    mastodon_username: str,
) -> None:

    print(f"Building digest from the past {hours} hours...")

    mst = Mastodon(
        access_token=mastodon_token,
        api_base_url=mastodon_base_url,
    )

    posts, boosts = fetch_posts_and_boosts(hours, mst, mastodon_username)

    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)


    digest_context = {
        "hours": hours,
        "posts": threshold_posts,
        "boosts": threshold_boosts,
        "mastodon_base_url": mastodon_base_url,
    }

    render_and_open_digest(digest_context)


if __name__ == "__main__":
    scorers = get_scorers()
    thresholds = get_thresholds()

    arg_parser = argparse.ArgumentParser(prog="mastodon_digest")
    arg_parser.add_argument(
        "-n",
        choices=range(1, 25),
        default=12,
        dest="hours",
        help="The number of hours to include in the Mastodon Digest",
        type=int,
    )
    arg_parser.add_argument(
        "-s",
        choices=list(scorers.keys()),
        default="SimpleWeighted",
        dest="scorer",
        help="""Which post scoring criteria to use. 
            SimpleWeighted is the default. 
            Simple scorers take a geometric mean of boosts and favs. 
            Extended scorers include reply counts in the geometric mean. 
            Weighted scorers multiply the score by an inverse sqaure root 
            of the author's followers, to reduce the influence of large accounts.
        """,
    )
    arg_parser.add_argument(
        "-t",
        choices=list(thresholds.keys()),
        default="normal",
        dest="threshold",
        help="""Which post threshold criteria to use. 
            Normal is the default.
            lax = 90th percentile
            normal = 95th percentile
            strict = 98th percentile
        """,
    )
    args = arg_parser.parse_args()

    mastodon_token = os.getenv("MASTODON_TOKEN")
    mastodon_base_url = os.getenv("MASTODON_BASE_URL")
    mastodon_username = os.getenv("MASTODON_USERNAME")

    if not mastodon_token:
        sys.exit("Missing environment variable: MASTODON_TOKEN")
    if not mastodon_base_url:
        sys.exit("Missing environment variable: MASTODON_BASE_URL")
    if not mastodon_username:
        sys.exit("Missing environment variable: MASTODON_USERNAME")

    run(
        args.hours,
        scorers[args.scorer](),
        get_threshold_from_name(args.threshold),
        mastodon_token,
        mastodon_base_url,
        mastodon_username,
    )
