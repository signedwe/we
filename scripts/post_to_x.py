"""Announce the latest post on X.

Two modes, chosen by whether the four credentials are set.

**Draft mode** (no credentials). Composes the post, checks it, writes it to
`agent/to_post.md` and into the workflow run summary as a copy-paste block. Costs
nothing and hands X no billing record. A human pastes it.

That last part gives up nothing the project actually claims. WE's claim is about
authorship — no human writes or edits the words. Pressing "post" on a line WE
wrote sits in the same category as paying for the compute and pointing the
telescope. Nobody is painting stars onto the lens.

**Live mode** (credentials present). Posts directly. Two calls, deliberately: the
idea goes out on its own, the link follows as a reply. X downranks link posts,
and the point is that the idea should survive in the timeline without anyone
clicking. That shape is also what the billing wants — since April 2026 a post
containing a URL costs $0.200 against $0.015 for one without.

Switching modes needs no code change. Add the four secrets and it starts posting;
remove them and it goes back to drafting.

This job is last in the workflow and nothing depends on it. The site is already
live by the time this runs, so a failure here is loud but harmless: the run goes
red, the post stays up. That is the right way round. Silence would be worse.

Usage:
    python scripts/post_to_x.py
    python scripts/post_to_x.py --dry-run   # composes and checks, writes nothing
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEST = ROOT / "agent" / "latest.json"
TO_POST = ROOT / "agent" / "to_post.md"
LIMIT = 280

CREDENTIALS = (
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
)


def note(line):
    """Print, and put it in the run summary where it will actually be seen."""
    print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def weighted_length(text):
    """X's own counting rules: most Latin text is one per character, emoji and
    CJK are two. Worth doing properly — a line that counts 280 to Python and 291
    to X gets rejected at the paste, or at the API after the money is spent."""
    total = 0
    for character in text:
        code = ord(character)
        cheap = (
            0x0000 <= code <= 0x10FF
            or 0x2000 <= code <= 0x200D
            or 0x2010 <= code <= 0x201F
            or 0x2032 <= code <= 0x2037
        )
        total += 1 if cheap else 2
    return total


def load_latest():
    if not LATEST.exists():
        note("No latest.json. Nothing was written, so nothing is announced.")
        return None

    try:
        latest = json.loads(LATEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        note(f"latest.json will not parse: {error}")
        sys.exit(1)

    short = (latest.get("short_version") or "").strip()
    url = (latest.get("url") or "").strip()

    if not short:
        note("latest.json carries no short_version. Refusing to post an empty post.")
        sys.exit(1)

    length = weighted_length(short)
    if length > LIMIT:
        note(
            f"short_version counts {length} against a limit of {LIMIT}. "
            "Not posting. Truncating someone's sentence to fit is worse than "
            "staying quiet, and this is the sort of thing that should be fixed "
            "in the writing rather than papered over here."
        )
        note(f"\n> {short}\n")
        sys.exit(1)

    if not url:
        note("No url in latest.json. Announcing without a reply.")

    return short, url, length


def draft(short, url, length, dry_run):
    """Write the post out for a human to paste, and say so loudly."""
    title = "## Ready to post\n"
    body = (
        f"{title}\n"
        f"Paste this as a new post on https://x.com/signedweai "
        f"({length} of {LIMIT} characters):\n\n"
        f"```\n{short}\n```\n"
    )
    if url:
        body += (
            "\nThen reply to it with the link, so the idea travels on its own "
            "and the link follows:\n\n"
            f"```\n{url}\n```\n"
        )
    body += (
        "\n---\n\nNo X credentials are set, so nothing was sent. That is the "
        "no-card path and it is a real option, not a degraded one: WE still "
        "wrote every word. Set the four secrets to have this posted "
        "automatically instead.\n"
    )

    print(body)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(body)

    if dry_run:
        print("Dry run. to_post.md not written.")
        return

    TO_POST.write_text(body, encoding="utf-8")
    print(f"Written to {TO_POST.relative_to(ROOT)}")


def publish(short, url, length):
    import tweepy

    note(f"Short version, {length} of {LIMIT}:\n\n> {short}\n")

    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )

    try:
        response = client.create_tweet(text=short)
    except tweepy.Forbidden as error:
        # 187 is X's duplicate-content rejection. It means this exact post has
        # already gone out — a re-run of the same workflow, most likely. That is
        # not a failure, it is the guard working.
        if "187" in str(error) or "duplicate" in str(error).lower():
            note("X rejected this as a duplicate. Already announced. Nothing to do.")
            return
        note(
            f"X refused the post: {error}\n\n"
            "A 403 here is nearly always the token, not the text. Tokens keep "
            "the permission level they were issued with, so if the app was set "
            "to Read-only when these were generated, changing it to Read and "
            "Write is not enough — the tokens have to be regenerated afterwards."
        )
        sys.exit(1)
    except tweepy.TweepyException as error:
        note(f"X posting failed: {error}")
        sys.exit(1)

    tweet_id = response.data["id"]
    note(f"Posted: https://x.com/signedweai/status/{tweet_id}")

    if not url:
        return

    try:
        client.create_tweet(text=url, in_reply_to_tweet_id=tweet_id)
        note("Link reply posted.")
    except tweepy.TweepyException as error:
        # The idea is out, which was the point. Flag the missing link and stop —
        # retrying would risk a second copy of the main post.
        note(f"Main post landed, link reply failed: {error}")
        sys.exit(1)


def main():
    dry_run = "--dry-run" in sys.argv

    loaded = load_latest()
    if loaded is None:
        return
    short, url, length = loaded

    if [name for name in CREDENTIALS if not os.environ.get(name)]:
        draft(short, url, length, dry_run)
        return

    if dry_run:
        note(f"Short version, {length} of {LIMIT}:\n\n> {short}\n")
        if url:
            note(f"Reply: {url}")
        note("\nDry run. Credentials present but nothing was sent.")
        return

    publish(short, url, length)


if __name__ == "__main__":
    main()
