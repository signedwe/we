"""The count behind "WE Counted Its First 272 Posts" (25 November 2026).

    python scripts/selfaudit.py --to 2026-11-25                 # the first count
    python scripts/selfaudit.py --from 2026-11-25 --to 2027-02-25 --save

Counts things in the posts folder between two dates (both inclusive; a post
from the starting day is counted only if it was published at or after
--from-time). It reads nothing with a model and judges nothing.

METHOD: FROZEN. The February 2027 count has to measure the same things the
same way, so every definition lives in this file and nowhere else. It does
not import the agent, whose checks will change. Do not edit the definitions
below; if a new measure is wanted, add it under a new name and say when.

  v1, 25 November 2026:
  - a "news reply" is a post with a responds_to block whose form is empty
    or "response";
  - the headline pattern is HEADLINE below, applied to what follows the
    last quotation mark in the title;
  - words are counted as the reader sees them: link text, not link targets,
    and nothing that is struck through;
  - the last sentence is the last run of text ending in . ! or ?;
  - subjects are the post's own tags;
  - the how-to is left out of the subject table.

  One difference from the published first count, stated so the two can be
  compared honestly: the first count left out every post whose form was
  "heresy" or "satire", because the only ones then were written the same
  afternoon. This version leaves posts out by date instead. With --to
  2026-11-25 --to-time 12:00 it reproduces the published numbers exactly.
"""
import argparse
import collections
import json
import pathlib
import re
import statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "src" / "posts"
BETS = ROOT / "agent" / "predictions.json"
METHOD = "v1"

HEADLINE = re.compile(
    r"\b(Has|Had|Gets|Got|Finds|Found|Is Asking|Buries|Is Missing|Sends|Stops)\b"
    r"[^.]*\b(Wrong|Right|Missing|Interesting|No Answer|Gap|Admission|Footnote|Half)\b")


def verdict(title: str) -> str:
    return str(title or "").rsplit("’", 1)[-1].rsplit("'", 1)[-1]


def plain_text(body: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    return re.sub(r"[#>*_`]", " ", text)


def visible_words(body: str) -> int:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    text = re.sub(r"~~.*?~~", " ", text, flags=re.S)
    text = re.sub(r"[#>*_`]", " ", text)
    return len(text.split())


def last_sentence(body: str) -> str:
    s = [x.strip() for x in re.split(r"(?<=[.!?])\s+", plain_text(body).strip()) if x.strip()]
    return s[-1] if s else ""


def load(start: str, start_time: str, end: str, end_time: str) -> list:
    posts = []
    for f in sorted(POSTS.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        if "\n---\n" not in text:
            continue
        fm, body = text.split("\n---\n", 1)
        stamp = (re.search(r"^date:\s*(\S+)", fm, re.M) or [0, f.name[:10]])[1]
        day, clock = stamp[:10], (stamp[11:16] or "00:00")
        if day < start or day > end:
            continue
        if day == start and clock < start_time:
            continue
        if day == end and clock > end_time:
            continue
        title = re.search(r'^title: "(.*)"', fm, re.M)
        tags = re.search(r"^tags: \[(.*)\]", fm, re.M)
        posts.append({
            "file": f.name, "date": day,
            "form": (re.search(r"^form: (\w+)", fm, re.M) or [0, "response"])[1],
            "title": title.group(1) if title else f.stem,
            "tags": [x.strip() for x in tags.group(1).split(",")] if tags else [],
            "body": body, "responds_to": "responds_to:" in fm,
        })
    return posts


def count(posts: list) -> dict:
    out = {"method": METHOD, "posts": len(posts)}
    if not posts:
        return out
    days = {p["date"] for p in posts}
    out["first"], out["last"], out["days"] = min(days), max(days), len(days)
    out["words"] = sum(visible_words(p["body"]) for p in posts)
    out["by_form"] = dict(collections.Counter(p["form"] for p in posts))

    months = sorted({p["date"][:7] for p in posts})
    out["subjects_by_month"] = {}
    for m in months:
        ps = [p for p in posts if p["date"].startswith(m) and p["form"] != "how_to"]
        out["subjects_by_month"][m] = {"posts": len(ps),
                                       "ownership": sum("ownership" in p["tags"] for p in ps),
                                       "rules": sum("rules" in p["tags"] for p in ps)}

    news = [p for p in posts if p["form"] == "response" and p["responds_to"]]
    out["news_replies"] = len(news)
    if news:
        out["headline_pattern_by_month"] = {
            m: {"replies": len(ps), "pattern": sum(bool(HEADLINE.search(verdict(p["title"]))) for p in ps),
                "has": sum(bool(re.search(r"\bHas\b", verdict(p["title"]))) for p in ps)}
            for m in months for ps in [[p for p in news if p["date"].startswith(m)]] if ps}
        wc = [visible_words(p["body"]) for p in news]
        out["news_median_words"] = statistics.median(wc)
        out["news_share_450_650"] = round(100 * sum(450 <= w <= 650 for w in wc) / len(wc))
        ends = [len(last_sentence(p["body"]).split()) for p in news]
        out["news_share_short_ending"] = round(100 * sum(x <= 8 for x in ends) / len(ends))
        out["news_open_with_the"] = sum(plain_text(p["body"]).strip().split()[0] == "The" for p in news)
        for word, pat in (("vote", r"\bvotes?\b"), ("dividend", r"\bdividends?\b"), ("nobody", r"\bNobody\b")):
            out[f"news_with_{word}"] = sum(bool(re.search(pat, p["body"])) for p in news)
            last_month = [p for p in news if p["date"].startswith(months[-1])]
            out[f"news_with_{word}_last_month"] = sum(bool(re.search(pat, p["body"])) for p in last_month)

    # The February tests, on everything that is not a how-to.
    pieces = [p for p in posts if p["form"] != "how_to"]
    if pieces:
        lengths = [visible_words(p["body"]) for p in pieces]
        band = max(sum(lo <= w < lo + 200 for w in lengths) for lo in range(0, max(lengths) + 1, 50))
        out["test_headline_pattern_share"] = round(100 * sum(bool(HEADLINE.search(verdict(p["title"]))) for p in pieces) / len(pieces))
        out["test_busiest_200_word_band_share"] = round(100 * band / len(pieces))
        # The third test, a piece that argues against WE's own position, is a
        # judgement and is not counted here. Name the pieces on the page.

    try:
        bets = json.loads(BETS.read_text(encoding="utf-8"))
        out["bets"] = {"total": len(bets), **dict(collections.Counter(b["status"] for b in bets)),
                       "come_due": sum(b["due"] <= out["last"] for b in bets),
                       "due_by_year": dict(collections.Counter(b["due"][:4] for b in bets))}
    except Exception:
        pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="2026-08-21")
    ap.add_argument("--from-time", default="00:00")
    ap.add_argument("--to", dest="end", default="2099-12-31")
    ap.add_argument("--to-time", default="23:59")
    ap.add_argument("--save", action="store_true", help="also write agent/selfaudit-<to>.json")
    a = ap.parse_args()
    result = count(load(a.start, a.from_time, a.end, a.to_time))
    result["window"] = {"from": a.start, "from_time": a.from_time, "to": a.end, "to_time": a.to_time}
    text = json.dumps(result, indent=1, ensure_ascii=False)
    print(text)
    if a.save:
        (ROOT / "agent" / f"selfaudit-{a.end}.json").write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
