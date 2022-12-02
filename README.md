# Mastodon Digest

This is a Python project that generates a digest of popular Mastodon posts from your home timeline. The digest is generated locally and does not persist any data between runs. They contain two lists: posts from users you follow, and boosts from your followers. Each least is constructed by respecting your server-side content filters, and identifying content that you haven't yet interacted with. Digests are automatically opened locally in your web browser. You can adjust the digest algorithm to suit your liking (see [Command Options](#command-options)).

![Mastodon Digest](https://i.imgur.com/ZRE9BKc.png)

## Local Configuration

From within your Python3 environment, simply:

```sh
pip isntall -r requirements.txt
```

### Set up the environment

Before you can run the tool locally, you need to copy [.env.example](./.env.example) to [.env](./.env) (which is ignored by git) and fill in the relevant environment variables:
 - `MASTODON_TOKEN` : This is your access token. You can generate on on your home instance under Preferences > Development.
 - `MASTODON_BASE_URL` : This is the protocol-aware URL of your Mastodon home instance. For example, if you are `@Gargron@mastodon.social`, then you would set `https://mastodon.social`.
 - `MASTODON_USERNAME`: This is your Mastodon account username on your home instance. For example, if you are `@Gargron@mastodon.social`, then you would set `Gargron`.

### Usage

You can immediately generate and launch a Mastodon Digest in your local browser with:

```sh
python run.py
```

A number of configuration flags are available to adjust the algorithm. You can see the command arguments by passing the `-h` flag:

```sh
python run.py -h
usage: mastodon_digest [-h]
                       [-n {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}]
                       [-s {ExtendedSimple,ExtendedSimpleWeighted,Simple,SimpleWeighted}]
                       [-t {lax,normal,strict}]

options:
  -h, --help            show this help message and exit
  -n {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}
                        The number of hours to include in the Mastodon Digest
  -s {ExtendedSimple,ExtendedSimpleWeighted,Simple,SimpleWeighted}
                        Which post scoring criteria to use. SimpleWeighted is the default.
                        Simple scorers take a geometric mean of boosts and favs. Extended
                        scorers include reply counts in the geometric mean. Weighted
                        scorers multiply the score by an inverse sqaure root of the
                        author's followers, to reduce the influence of large accounts.
  -t {lax,normal,strict}
                        Which post threshold criteria to use. Normal is the default. lax =
                        90th percentile normal = 95th percentile strict = 98th percentile
```

#### Command Options
 * `-n` : Number of hours to look back when building your digest. This can be an integer from 1 to 24. Defaults to **12**. I've found that 12 works will in the morning and 8 works well in the evening.
 * `-s` : Scoring method to use. **SimpleWeighted** is the default.
   - `Simple` : Each post is scored with a [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) of its number of boosts and its number of favorites.
   - `SimpleWeighted` : The same as `Simple`, but every score is multiplied by the inverse of the square root of the author's follower count. Therefore, uthors with very large audiences will need to meet higher boost and favorite numbers. **This is the default scorer**.
   - `ExtendedSimple` : Each post is scored with a [geometric mean](https://en.wikipedia.org/wiki/Geometric_mean) of its number of boosts, its number of favorites, and its number of replies.
   - `ExtendedSimpleWeighted` : The same as `ExtendedSimple`, but every score is multiplied by the inverse of the square root of the author's follower count. Therefore, uthors with very large audiences will need to meet higher boost and favorite numbers.
* `-t` : Threshold for scores to include. normal is the default
  - `lax` : Posts must achieve a score within the 90th percentile.
  - `normal` : Posts must achieve a score within the 95th percentile. **This is the default threshold**.
  - `strict` : Posts must achive a score within the 98th percentile.

## What's missing?

Probably many things!

You likely noticed that this repository has no tests. That's because I'm still treating this as a toy and not work. But tests might be good!

I'm still thinking about the best structure / process / whatever to incorporate new interesting algorithms. Maybe I'll devote time to that, maybe not, but you can always fork.

## A Matt Hodges project

This project is maintained by [@MattHodges](https://mastodon.social/@MattHodges).

_Please use it for good, not evil._