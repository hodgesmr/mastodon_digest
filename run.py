import argparse
import os
import sys
import tempfile
import webbrowser
from datetime import datetime, timedelta, timezone
from math import sqrt

from scipy import stats

from mastodon import Mastodon


def calculate_score(post):

    # geometric mean of boosts and favs
    metric_averae = stats.gmean([post["reblogs_count"], post["favourites_count"]])

    # if they have no followers, I don't want to trust any amount of boosts or favs; zero it out
    if post["account"]["followers_count"] == 0: 
        weight = 0
    else:
        # inversely weight against how big the account is
        weight = 1/sqrt(post["account"]["followers_count"])

    return metric_averae * weight
    

def run(hours, mastodon_token, mastodon_base_url, mastodon_username):

    mst = Mastodon(
        access_token=mastodon_token,
        api_base_url=mastodon_base_url,
    )

    start = datetime.now(timezone.utc) - timedelta(hours=hours)

    posts = []
    boosts = []

    print(f"Fetching posts from the past {hours} hours...")

    next_kwargs = {
        "min_id": start,
    }
    max_seen_id = -1
    seen = set({})

    while next_kwargs:  # go until we have no more pagination kwargs
        response = mst.timeline(**next_kwargs)

        for post in response:
            original_id = post["id"]
            boost = False
            if post["reblog"] is not None:
                post = post["reblog"]  # look at the bosted post
                boost = True

            url = post["url"]

            if url not in seen:
                info = {
                    "url": url,
                    "redirect_url": f"{mastodon_base_url}/authorize_interaction?uri={url}",
                    "created": post["created_at"],
                    "content": post["content"],
                    "username": post["account"]["username"],
                    "acct": post["account"]["acct"],
                    "acct_followers": post["account"]["followers_count"],
                    "boosts": post["reblogs_count"],
                    "favs": post["favourites_count"],
                    "boosted_by_me": post["reblogged"],
                    "favd_by_me": post["favourited"],
                    "score": calculate_score(post),
                }
                if (
                    not info["boosted_by_me"]
                    and not info["favd_by_me"]
                    and info["acct"] != mastodon_username
                    and info["score"] > 0
                ):
                    if boost:
                        boosts.append(info)
                    else:
                        posts.append(info)
                    seen.add(url)

            # idk why the library's pagination isn't working, do it manually
            if original_id > max_seen_id:
                max_seen_id = original_id

        if response:
            next_kwargs = {"min_id": max_seen_id + 1}
        else:
            next_kwargs = None

    post_scores = [post["score"] for post in posts]
    boost_scores = [boost["score"] for boost in boosts]

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
    posts_header = '<h2 style="color:white;">Here are some popular posts you may have missed:</h2>'
    boosts_header = '<h2 style="color:white;">Here are some popular boosts you may have missed:</h2>'
    container_close = "</div>"
    body_close = "</body>"
    html_close = "</html>"

    content_collection = [
        [posts, post_scores, ""],
        [boosts, boost_scores, ""],
    ]

    print("Selecting posts...")
    for c in content_collection:
        for post in c[0]:
            percentile = stats.percentileofscore(c[1], post["score"])
            if percentile > 95:
                c[2] += (
                    '<div class="post">'
                    f'<a style="color:white;" href=\'{post["redirect_url"]}\' target="_blank">Home Link</a>'
                    '<span style="color:white;"> | </span>'
                    f'<a style="color:white;" href=\'{post["url"]}\' target="_blank">Original Link</a>'
                    "<br />"
                    f'<iframe src=\'{post["url"]}/embed\' class="mastodon-embed" style="max-width: 100%; border: 0" width="400" allowfullscreen="allowfullscreen"></iframe>'
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


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(prog='mastodon_digest')
    arg_parser.add_argument('hours', type=int, choices=range(1, 25), help="The number of hours to include in the Mastodon Digest")
    args = arg_parser.parse_args()
    if not args.hours:
        arg_parser.print_help()
    else:
        mastodon_token = os.getenv('MASTODON_TOKEN')
        mastodon_base_url = os.getenv('MASTODON_BASE_URL')
        mastodon_username = os.getenv('MASTODON_USERNAME')

        if not mastodon_token:
            sys.exit('Missing environment variable: MASTODON_TOKEN')
        if not mastodon_base_url:
            sys.exit('Missing environment variable: MASTODON_BASE_URL')
        if not mastodon_username:
            sys.exit('Missing environment variable: MASTODON_USERNAME')
        
        run(args.hours, mastodon_token, mastodon_base_url, mastodon_username)