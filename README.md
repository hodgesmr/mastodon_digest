# Mastodon Digest

This is a Python project that generates a digest of popular Mastodon posts from your home timeline. The digest is generated locally. The digests present two lists: posts from users you follow, and boosts from your followers. Each list is constructed by respecting your server-side content filters and identifying content that you haven't yet interacted with. Digests are automatically opened locally in your web browser. You can adjust the digest algorithm to suit your liking (see [Command arguments](#command-arguments)). The digest will not contain posts from users who include `#nobot` or `#noindex` in their bio.

![Mastodon Digest](https://i.imgur.com/ZRE9BKc.png)

## Run

You can run in [Docker](#docker) or in a [local python environment](#local). But first, set up your environment:

Before you can run the tool locally, you need to copy [.env.example](./.env.example) to `.env` (which is ignored by git) and fill in the relevant environment variables:

```sh
cp .env.example .env
```

 - `MASTODON_TOKEN` : This is your access token. You can generate one on your home instance under Preferences > Development. Your token only needs Read permissions.
 - `MASTODON_BASE_URL` : This is the protocol-aware URL of your Mastodon home instance. For example, if you are `@Gargron@mastodon.social`, then you would set `https://mastodon.social`.

Both the Docker container and the python script will construct the environment from the `.env` file. This is usually sufficient and you can stop here. However, you may **optionally** construct your environment manually. This is may be useful for deployed environments.

### Docker

First, build the image:

```sh
make build
```

Then you can generate and open a digest:

```sh
make run
```

You can also pass [command arguments](#command-arguments):

```sh
make run FLAGS="-n 8 -s ExtendedSimpleWeighted -t lax"
```

### Local

Mastodon Digest has been tested to work on Python 3.9 and above.

#### With Make

If your system Python meets that, you can:

```sh
make local
```

You can also pass [command arguments](#command-arguments):

```sh
make local FLAGS="-n 8 -s ExtendedSimpleWeighted -t lax"
```

#### Manually

Althernatively if you have a different Python 3.9 environment, you can:

```sh
pip install -r requirements.txt
```

Then generate a Mastodon Digest with:

```sh
python run.py
```

Through either method, the digest is written to `render/index(<RUN INFO>).html` by default. You can then view it with the browser of your choice.


## Command arguments

A number of command arguments are available to adjust the algorithm. You can see the command arguments by passing the `-h` flag:

```sh
python run.py -h
```

```
usage: mastodon_digest [-h] [-f TIMELINE] [-n {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}]
                       [-s {ExtendedSimple,ExtendedSimpleWeighted,Simple,SimpleWeighted}] [-t {lax,normal,strict}]
                       [-o OUTPUT_PATH] [--theme {light,default}]

options:
  -h, --help            show this help message and exit
  -f TIMELINE           The timeline to summarize: Expects 'home', 'local' or 'federated', or 'list:id', 'hashtag:tag' (default:
                        home)
  -n {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}
                        The number of hours to include in the Mastodon Digest (default: 12)
  -s {ExtendedSimple,ExtendedSimpleWeighted,Simple,SimpleWeighted}
                        Which post scoring criteria to use. Simple scorers take a geometric mean of boosts and favs. Extended
                        scorers include reply counts in the geometric mean. Weighted scorers multiply the score by an inverse
                        square root of the author's followers, to reduce the influence of large accounts. (default:
                        SimpleWeighted)
  -t {lax,normal,strict}
                        Which post threshold criteria to use. lax = 90th percentile, normal = 95th percentile, strict = 98th
                        percentile (default: normal)
  -o OUTPUT_PATH        Output file or directory for the rendered digest (default: ./render/, which creates an file 'index(<RUN INFO>).html' in the directory 'render')
  --theme {light,default}
                        Named template theme with which to render the digest (default: default)
```

If you are running with Docker and make, you can pass flags as:

```sh
make run FLAGS="-n 8 -s ExtendedSimpleWeighted -t lax"
```

#### Algorithm Options
 * `-f` : Timeline feed to source from. **home** is the default.
    - `home` : Your home timeline.
    - `local` : The local timeline for your instance; all the posts from users in an instance. This is more useful on small/medium-sized instances. Consider using a much smaller value for `-n` to limit the number of posts analysed.
    - `federated` : The federated public timeline on your instance; all posts that your instance has seen. This is useful for discovering posts on very small or personal instances.
    - `hashtag:HashTagName` : The timeline for the specified #hashtag. (Do not include the `#` in the name.)
    - `list:3` : A list timeline. Lists are given numeric IDs (as in their URL, e.g. `https://example.social/lists/2`), which you must use for input here, not the list name.
 * `-n` : Number of hours to look back when building your digest. This can be an integer from 1 to 24. Defaults to **12**. I've found that 12 works well in the morning and 8 works well in the evening.
 * `-s` : Scoring method to use. **SimpleWeighted** is the default.
    - `Simple` : Each post is scored with a modified [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) of its number of boosts and its number of favorites.
    - `SimpleWeighted` : The same as `Simple`, but every score is multiplied by the inverse of the square root of the author's follower count. Therefore, authors with very large audiences will need to meet higher boost and favorite numbers. **This is the default scorer**.
    - `ExtendedSimple` : Each post is scored with a modified [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) of its number of boosts, its number of favorites, and its number of replies.
    - `ExtendedSimpleWeighted` : The same as `ExtendedSimple`, but every score is multiplied by the inverse of the square root of the author's follower count. Therefore, authors with very large audiences will need to meet higher boost, favorite, and reply numbers.
* `-t` : Threshold for scores to include. **normal** is the default
    - `lax` : Posts must achieve a score within the 90th percentile.
    - `normal` : Posts must achieve a score within the 95th percentile. **This is the default threshold**.
    - `strict` : Posts must achive a score within the 98th percentile.

I'm still experimenting with these, so it's possible that I change the defaults in the future.

#### Theme Options

Specify a render template theme with the `--theme <theme-name>` argument.

Two basic templates for the digest are provided, `default` and `light`. You can create new templates by adding a directory to `templates/themes/my-theme/`. You must create `index.html.jinja` as the root template.

Template fragments placed inside `themes/common/` can be re-used by any template, which is helpful to try and keep things DRY-er (for example, include `scripts.html.jinja` for the current version of the Mastodon iframe embed JavaScript.)

The available view variables are:

* `posts` : Array of posts to display
* `boosts` : Array of boosts to display
* `hours` : Hours rendered
* `mastodon_base_url` : The base URL for this mastodon instance, as defined in env.
* `rendered_at` : The time the digest was generated
* `timeline_name` : The timeline used to generated the digest (e.g. home, local, hashtag:introductions)
* `threshold` : The threshold for scores included
* `scorer` : The scoring method used

Each post and boost is a `ScoredPost` object:

* `url` : The canonical URL of the post.
* `get_home_url(mastodon_base_url)`: The URL of the post, translated to the `mastodon_base_url` instance provided.
* `info` : The full underlying `status` dict for the post, [documented by mastodon.py here](https://mastodonpy.readthedocs.io/en/stable/02_return_values.html#status-dicts).

When developing themes, you can run the digest in development mode, which uses theme files from the local filesystem rather than rebuilding the docker image every time you make a change:

```sh
make dev FLAGS="--theme my-theme"
```

## What's missing?

Probably many things!

You likely noticed that this repository has no tests. That's because I'm still treating this as a toy and not work. But tests might be good!

I'm still thinking about the best structure / process / whatever to incorporate new interesting algorithms. Maybe I'll devote time to that, maybe not.

I've tested this on my Intel and M1 macOS machines. Ubuntu users say it works. I believe it'll work on other architectures and operating systems, but I haven't tried. The availability of a GUI web browser is important. [Do you know how to make it work on Windows?](https://github.com/hodgesmr/mastodon_digest/issues/13)

## A Matt Hodges project

This project is maintained by [@MattHodges](https://mastodon.social/@MattHodges).

_Please use it for good, not evil._
