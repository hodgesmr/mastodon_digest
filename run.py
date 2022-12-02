import argparse
import os
import sys
import tempfile
import webbrowser
from datetime import datetime, timedelta, timezone

from mastodon import Mastodon
from scipy import stats

from models import ScoredPost
from scorers import get_scorers
from thresholds import get_thresholds


def run(hours, scorer, threshold, mastodon_token, mastodon_base_url, mastodon_username):

    scorer = scorer()

    mst = Mastodon(
        access_token=mastodon_token,
        api_base_url=mastodon_base_url,
    )

    # First, get our filters
    filters = mst.filters()

    start = datetime.now(timezone.utc) - timedelta(hours=hours)

    scored_posts = []
    scored_boosts = []

    print(f"Fetching posts from the past {hours} hours...")

    seen = set({})

    response = mst.timeline(min_id=start)

    while response:  # go until we have no more pagination results

        # apply our filters
        filtered_response = mst.filters_apply(response, filters, "home")

        for post in filtered_response:
            boost = False
            if post["reblog"] is not None:
                post = post["reblog"]  # look at the bosted post
                boost = True

            scored_post = ScoredPost(post)

            if scored_post.url not in seen:
                if (
                    not scored_post.info["reblogged"]
                    and not scored_post.info["favourited"]
                    and not scored_post.info["bookmarked"]
                    and scored_post.info["account"]["acct"] != mastodon_username
                ):
                    if boost:
                        scored_boosts.append(scored_post)
                    else:
                        scored_posts.append(scored_post)
                    seen.add(scored_post.url)

        response = mst.fetch_previous(
            response
        )  # fext the previous (because of reverse chron) page of results

    post_scores = [scored_post.get_score(scorer) for scored_post in scored_posts]
    boost_scores = [scored_boost.get_score(scorer) for scored_boost in scored_boosts]

    # todo - do all this nonsense in Jinja or something better
    html_open = "<!DOCTYPE html>" "<html>"
    head = (
        "<head>"
        '<script src="https://static-cdn.mastodon.social/embed.js" async="async"></script>'
        "</head>"
    )
    body_open = '<body bgcolor="#292c36" style="font-family: Arial, sans-serif;">'
    container_open = '<div id="container" style="margin: auto; max-width: 640px; padding: 10px; text-align: center;">'
    title = '<h1 style="color:white;">Mastodon Digest</h1>'
    subtitle = f'<h3 style="color:#D3D3D3;"><i>Sourced from your timeline over the past {hours} hours</i></h2>'
    posts_header = (
        '<h2 style="color:white;">Here are some popular posts you may have missed:</h2>'
    )
    boosts_header = '<h2 style="color:white;">Here are some popular boosts you may have missed:</h2>'
    container_close = "</div>"
    body_close = "</body>"
    html_close = "</html>"

    content_collection = [
        [scored_posts, post_scores, ""],
        [scored_boosts, boost_scores, ""],
    ]

    print("Selecting posts...")
    for c in content_collection:
        for post in c[0]:
            percentile = stats.percentileofscore(c[1], post.get_score(scorer))
            if percentile > threshold:
                c[2] += (
                    '<div class="post">'
                    f'<a style="color:white;" href=\'{post.get_home_url(mastodon_base_url)}\' target="_blank">Home Link</a>'
                    '<span style="color:white;"> | </span>'
                    f'<a style="color:white;" href=\'{post.url}\' target="_blank">Original Link</a>'
                    "<br />"
                    f'<iframe src=\'{post.url}/embed\' class="mastodon-embed" style="max-width: 100%; border: 0" width="400" allowfullscreen="allowfullscreen"></iframe>'
                    "<br /><br />"
                    "</div>"
                )

    output_html = (
        f"{html_open}"
        f"{head}"
        f"{body_open}"
        f"{container_open}"
        f"{title}"
        f"{subtitle}"
        f"{posts_header}"
        f"{content_collection[0][2]}"  # posts
        f"{boosts_header}"
        f"{content_collection[1][2]}"  # boosts
        f"{container_close}"
        f"{body_close}"
        f"{html_close}"
    )

    print("Saving document...")
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as out_file:
        final_url = f"file://{out_file.name}"
        out_file.write(output_html)

    print("Opening browser...")
    webbrowser.open(final_url)


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
        """
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
        """
    )
    args = arg_parser.parse_args()
    if not args.hours:
        arg_parser.print_help()
    else:
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
            scorers[args.scorer],
            thresholds[args.threshold],
            mastodon_token,
            mastodon_base_url,
            mastodon_username,
        )
