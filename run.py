from __future__ import annotations

import argparse
import dotenv
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from urllib3.util.url import parse_url
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader
from mastodon import Mastodon

from api import fetch_posts_and_boosts
from scorers import get_scorers, ConfiguredScorer
from thresholds import get_threshold_from_name, get_thresholds

if TYPE_CHECKING:
    from scorers import Scorer
    from thresholds import Threshold
    from argparse import Namespace, ArgumentParser


def render_digest(context: dict, output_dir: Path, theme: str = "default") -> None:
    environment = Environment(
        loader=FileSystemLoader([f"templates/themes/{theme}", "templates/common"])
    )
    template = environment.get_template("index.html.jinja")
    output_html = template.render(context)
    output_file_path = output_dir / "index.html"
    output_file_path.write_text(output_html)


def list_themes() -> list[str]:
    # Return themes, named by directory in `/templates/themes` and which have an `index.html.jinja` present.
    return list(
        filter(
            lambda dir_name: not dir_name.startswith(".")
            and os.path.exists(f"templates/themes/{dir_name}/index.html.jinja"),
            os.listdir("templates/themes"),
        )
    )


def format_base_url(mastodon_base_url: str) -> str:
    return mastodon_base_url.strip().rstrip("/")


def check_config_pars(pars):
    for acct_list in ["amplify_accounts"]:
        for acct in pars.get(acct_list, []):
            if len(acct.split("@")) != 2:
                sys.exit("Please provide accounts in the form 'user@host' (check failed for '%s' in list '%s')"%(acct, acct_list)) 


def add_defaults_from_config(arg_parser : ArgumentParser, config_file : Path) -> None:
    # Override defaults of parser by pars given in config file
    if config_file.exists() and config_file.is_file():
        with open(config_file, "r") as f:
            cfg_pars = yaml.safe_load(f)
        print("Loading config file '%s'"%config_file)
        check_config_pars(cfg_pars)
        arg_parser.set_defaults(**cfg_pars)

    else:
        if str(config_file) != arg_parser.get_default("config"):
            print("Couldn't load config file '%s'."%config_file)
                

def run(
    hours: int,
    scorer: Scorer,
    threshold: Threshold,
    mastodon_token: str,
    mastodon_base_url: str,
    timeline: str,
    output_dir: Path,
    theme: str,
) -> None:

    print(f"Building digest from the past {hours} hours...")

    mst = Mastodon(
        access_token=mastodon_token,
        api_base_url=mastodon_base_url,
    )

    # 1. Fetch all the posts and boosts from our home timeline that we haven't interacted with
    posts, boosts = fetch_posts_and_boosts(hours, mst, timeline)

    # 2. Score them, and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)

    # 3. Sort posts and boosts by score, descending
    threshold_posts = sorted(
        threshold_posts, key=lambda post: post.get_score(scorer), reverse=True
    )
    threshold_boosts = sorted(
        threshold_boosts, key=lambda post: post.get_score(scorer), reverse=True
    )

    # 4. Build the digest
    if len(threshold_posts) == 0 and len(threshold_boosts) == 0:
        sys.exit(
            f"No posts or boosts were found for the provided digest arguments. Exiting."
        )
    else:
        render_digest(
            context={
                "hours": hours,
                "posts": threshold_posts,
                "boosts": threshold_boosts,
                "mastodon_base_url": mastodon_base_url,
                "rendered_at": datetime.utcnow().strftime("%B %d, %Y at %H:%M:%S UTC"),
                "timeline_name": timeline,
                "threshold": threshold.get_name(),
                "scorer": scorer.get_name(),
            },
            output_dir=output_dir,
            theme=theme,
        )


if __name__ == "__main__":
    scorers = get_scorers()
    thresholds = get_thresholds()

    arg_parser = argparse.ArgumentParser(
        prog="mastodon_digest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    arg_parser.add_argument(
        "-f",  # for "feed" since t-for-timeline is taken
        default="home",
        dest="timeline",
        help="The timeline to summarize: Expects 'home', 'local' or 'federated', or 'list:id', 'hashtag:tag'",
        required=False,
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
            Weighted scorers multiply the score by an inverse square root
            of the author's followers, to reduce the influence of large accounts.
        """,
    )
    arg_parser.add_argument(
        "-c", "--config",
        default="./cfg.yaml",
        dest="config",
        help="Defines a configuration file.",
        required=False,
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
    arg_parser.add_argument(
        "--theme",
        choices=list_themes(),
        default="default",
        dest="theme",
        help="Named template theme with which to render the digest",
        required=False,
    )
    add_defaults_from_config(arg_parser, Path(arg_parser.parse_args().config))
    # Parse args once more with updated defaults
    args = arg_parser.parse_args()

    # Attempt to validate the output directory
    output_dir = Path(args.output_dir)
    if not output_dir.exists() or not output_dir.is_dir():
        sys.exit(f"Output directory not found: {args.output_dir}")

    # Loosely validate the timeline argument, so that if a completely unexpected string is entered,
    # we explicitly reset to 'Home', which makes the rendered output cleaner.
    timeline = args.timeline.strip().lower()
    validTimelineTypes = ["home", "local", "federated", "hashtag", "list"]
    timelineType, *_ = timeline.split(":", 1)
    if not timelineType in validTimelineTypes:
        timeline = "home"

    # load and validate env
    dotenv.load_dotenv(override=False)

    mastodon_token = os.getenv("MASTODON_TOKEN")
    print("token:", mastodon_token)
    mastodon_base_url = os.getenv("MASTODON_BASE_URL")

    if not mastodon_token:
        sys.exit("Missing environment variable: MASTODON_TOKEN")
    if not mastodon_base_url:
        sys.exit("Missing environment variable: MASTODON_BASE_URL")

    # Check if a ConfiguredScorer should be used 
    # NOTE: depends on whether the parameters in the config file require this, currently,
    #       but may be changed to always use a ConfiguredScorer as a wrapper)
    if set(vars(args)).intersection(ConfiguredScorer.get_additional_scorer_pars()):
        # At least one parameter was passed, which requires 
        # the use of a ConfiguredScorer to modify scores of the base scorer
        scorer = ConfiguredScorer(base_scorer=args.scorer, 
                                  default_host=parse_url(mastodon_base_url).hostname, 
                                  **vars(args))
    else:
        scorer = scorers[args.scorer]()
        
    run(
        args.hours,
        scorer,
        get_threshold_from_name(args.threshold),
        mastodon_token,
        format_base_url(mastodon_base_url),
        timeline,
        output_dir,
        args.theme,
    )
