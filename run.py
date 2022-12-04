from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader
from mastodon import Mastodon

from api import fetch_posts_and_boosts
from scorers import get_scorers
from thresholds import get_threshold_from_name, get_thresholds

if TYPE_CHECKING:
    from scorers import Scorer
    from thresholds import Threshold


def render_digest(context: dict, output_dir: Path) -> None:
    environment = Environment(loader=FileSystemLoader("templates/"))
    template = environment.get_template("digest.html.jinja")
    output_html = template.render(context)
    output_file_path = output_dir / 'index.html'
    output_file_path.write_text(output_html)


def run(
    hours: int,
    scorer: Scorer,
    threshold: Threshold,
    mastodon_token: str,
    mastodon_base_url: str,
    mastodon_username: str,
    output_dir: Path,
) -> None:

    print(f"Building digest from the past {hours} hours...")

    mst = Mastodon(
        access_token=mastodon_token,
        api_base_url=mastodon_base_url,
    )

    # 1. Fetch all the posts and boosts from our home timeline that we haven't interacted with
    posts, boosts = fetch_posts_and_boosts(hours, mst, mastodon_username)

    # 2. Score them, and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)

    # 3. Build the digest
    render_digest(
        context={
            "hours": hours,
            "posts": threshold_posts,
            "boosts": threshold_boosts,
            "mastodon_base_url": mastodon_base_url,
        },
        output_dir=output_dir,
    )


if __name__ == "__main__":
    scorers = get_scorers()
    thresholds = get_thresholds()

    arg_parser = argparse.ArgumentParser(
        prog="mastodon_digest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
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
            lax = 90th percentile,
            normal = 95th percentile,
            strict = 98th percentile
        """,
    )
    arg_parser.add_argument(
        "-o",
        default="./render/",
        dest="output_dir",
        help="Output directory for the rendered digest",
        required=False,
    )
    args = arg_parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        sys.exit(f"Output directory not found: {args.output_dir}")

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
        output_dir,
    )
