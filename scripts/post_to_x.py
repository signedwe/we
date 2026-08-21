#!/usr/bin/env python3
"""Post the short version to X, with the link in a reply.

Idea-first: X downranks link posts, and the point is that the idea should
survive in the timeline without anyone clicking.
"""
import json
import os
import pathlib
import sys

import tweepy

LATEST = pathlib.Path(__file__).resolve().parent.parent / "agent" / "latest.json"


def main() -> int:
    if not LATEST.exists():
        print("No latest.json — nothing to post.")
        return 0

    latest = json.loads(LATEST.read_text(encoding="utf-8"))

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )

    main_post = client.create_tweet(text=latest["short_version"])
    client.create_tweet(
        text=latest["url"], in_reply_to_tweet_id=main_post.data["id"]
    )
    print(f"Posted: {latest['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
