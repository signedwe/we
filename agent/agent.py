#!/usr/bin/env python3
"""
WE — the writer.

Reads its public brief and its own running agenda, writes one post,
saves it to the site, and updates the agenda for next time.

Everything it publishes is unedited model output. The only human inputs
are brief.md and agenda.md, both public, both in this repo.

The brief checks below never rewrite the model's words. They hand the
failures back and make it write again. If it still can't hit the brief
after two goes, the post is saved as written and the failures are
printed loudly. Publishing an unedited miss is honest. Quietly patching
it with string surgery is not.
"""

import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

import anthropic

ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEF = ROOT / "agent" / "brief.md"
AGENDA = ROOT / "agent" / "agenda.md"
POSTS = ROOT / "src" / "posts"
LATEST = ROOT / "agent" / "latest.json"
# What the critic said, run after run. WE reads this file and cannot write
# to it. The agenda is WE's account of itself; this is somebody else's.
CRITIC = ROOT / "agent" / "critic.md"
# Every prediction WE has made, with the date it comes due. Nothing scores
# them yet. The point for now is that they exist somewhere they cannot be
# quietly forgotten.
PREDICTIONS = ROOT / "agent" / "predictions.md"
# WE's developing account of what is happening. Rewritten by WE each run,
# but only by adding to the top: the old versions stay underneath.
THESIS = ROOT / "agent" / "thesis.md"

MODEL = "claude-sonnet-4-6"
SITE = "https://signedwe.github.io/we"

# Server-side web search. The API runs the searches itself inside the one
# request, so there is no tool loop to write here. It comes back as extra
# content blocks.
TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

# The critic gets its own smaller search budget, enough to sanity-check what
# a cited source actually is.
CRITIC_TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]

WORD_LIMIT = 600
MAX_RETRIES = 2
EM_DASH = "—"
# Substrings, not whole words. "scarce" catches "scarcely", "scarcity"
# catches "scarcities". The brief says any form, ever.
BANNED = ("artefact", "artifact", "scarcity", "scarce")

# If a post leans on a job, somebody who does that job gets a short reply.
# The bench argues about the arrangement; none of them has ever done the work.
PROFESSIONS = (
    "lawyer", "solicitor", "barrister", "paralegal", "conveyancer",
    "doctor", "gp", "surgeon", "nurse", "paramedic", "pharmacist",
    "dentist", "vet", "therapist", "counsellor", "midwife",
    "teacher", "lecturer", "accountant", "auditor", "actuary",
    "architect", "surveyor", "engineer", "electrician", "plumber",
    "pilot", "driver", "translator", "interpreter", "journalist",
    "editor", "librarian", "archivist", "social worker", "radiographer",
    "radiologist", "physiotherapist", "optometrist", "psychiatrist",
    "consultant", "clinician", "inspector", "examiner", "underwriter",
    "recruiter", "actuary", "bookkeeper", "planner", "valuer",
)

# Phrases that stop a post dead to award the writer a medal for fairness.
# The concession stays. The announcement of it goes.
DEFLATING = (
    "there is a genuine argument",
    "there is a decent case",
    "there is a serious objection",
    "the honest objection",
    "the fair objection",
    "to be fair",
    "it should be said",
    "it must be said",
    "in fairness",
    "that said,",
    "of course, there",
    "it is worth noting",
    "it's worth noting",
    "it is important to note",
)

# Hedges. Each one buys the writer an escape route and costs the reader a
# reason to care. The brief asks for the strong version, said plainly.
HEDGES = (
    "arguably", "it could be argued", "one might argue", "it might be argued",
    "in many ways", "to some degree", "to some extent", "somewhat",
    "it seems fair to say", "on balance it", "relatively speaking",
    "it is probably fair", "more or less", "in a sense",
)

# "X is Y" describes a state. Nothing happens in it. Measured against the
# voice this brief is aiming at, which runs near 30 per cent, anything past
# 45 reads as a list of conditions rather than a piece of writing.
COPULA = re.compile(r"\b(is|are|was|were|be|been|being|it's|that's|there's)\b", re.I)
COPULA_CEILING = 45

# Announcing the next paragraph instead of writing it.
SIGNPOSTS = (
    "here is what happened", "here is what", "the interesting question",
    "the interesting part", "the interesting thing", "now the bit",
    "so here is", "here is the bet", "the point is", "what is really going on",
    "what's really going on", "it is worth noting", "let me explain",
    "i want to", "consider this", "the thing is", "here's the thing",
    "which brings me to", "before we go on", "bear with me",
)

# Dead metaphors. Each one is an abstraction wearing a picture's clothes.
DEAD_IMAGES = (
    "landscape", "ecosystem", "journey", "unpack", "through the lens",
    "double-edged sword", "tip of the iceberg", "sea change", "paradigm",
    "at a crossroads", "the elephant in the room", "moving the goalposts",
)

# Libel guard. An accusing word in the same sentence as a name is the shape
# of a claim about a person, and the person who runs WE carries the legal
# risk for it. Deliberately crude: it over-triggers, and a false alarm costs
# one rewrite.
ACCUSATIONS = (
    "corrupt",
    "fraud",
    "fraudulent",
    "dishonest",
    "lying",
    "liar",
    "crooked",
    "incompetent",
    "negligent",
    "rigged",
    "scam",
    "cover-up",
    "bribe",
)


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:60]


def recent_posts(n: int = 8) -> str:
    """Titles of what WE has already published, so it doesn't repeat itself."""
    files = sorted(POSTS.glob("*.md"), reverse=True)[:n]
    out = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        m = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        if m:
            out.append(f"- {m.group(1)}")
    return "\n".join(out) if out else "(nothing published yet, this is the first post)"


# --------------------------------------------------------------------------
# reading the response
# --------------------------------------------------------------------------


def text_blocks(resp) -> list:
    """The model's own words, in order.

    With search on, resp.content also holds server_tool_use and
    web_search_tool_result blocks. Those aren't text and are skipped.
    """
    return [b.text for b in resp.content if getattr(b, "type", None) == "text"]


def harvest_sources(resp) -> list:
    """Every page the search actually returned: title and url, in order.

    A web_search_tool_result block holds a list of results, or an error
    object if that search failed. Only the lists are worth anything.
    """
    found = []
    for b in resp.content:
        if getattr(b, "type", None) != "web_search_tool_result":
            continue
        items = getattr(b, "content", None)
        if not isinstance(items, list):
            continue  # the search errored
        for it in items:
            url = getattr(it, "url", None)
            if not url:
                continue
            title = (getattr(it, "title", None) or url).strip()
            found.append({"title": title, "url": url})
    return found


def merge_sources(existing: list, new: list) -> list:
    """Add what we haven't seen, keeping first-seen order."""
    seen = {s["url"] for s in existing}
    for s in new:
        if s["url"] not in seen:
            seen.add(s["url"])
            existing.append(s)
    return existing


def extract_json(blocks: list, require=("title", "body")) -> dict:
    """Find the post JSON.

    The model narrates between searches, so there are several text blocks
    and the early ones can hold stray braces. The JSON is in the last one.
    Try that first, walk backwards, and only then fall back to the whole
    transcript.
    """
    candidates = [b for b in reversed(blocks) if b.strip()]
    candidates.append("\n".join(blocks))

    for chunk in candidates:
        chunk = re.sub(r"^```(?:json)?\s*|\s*```$", "", chunk.strip())
        start, end = chunk.find("{"), chunk.rfind("}")
        if start == -1 or end == -1:
            continue
        try:
            data = json.loads(chunk[start : end + 1])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and all(k in data for k in require):
            return data

    joined = "\n".join(blocks)
    raise ValueError(f"No post JSON found in model output:\n{joined[:1000]}")


def clean_sources(raw) -> list:
    """Whatever the model put in "sources", reduced to usable pairs."""
    out, seen = [], set()
    if not isinstance(raw, list):
        return out
    for s in raw:
        if not isinstance(s, dict):
            continue
        url = str(s.get("url") or "").strip()
        title = str(s.get("title") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({"title": title or url, "url": url})
    return out


# --------------------------------------------------------------------------
# the brief, enforced
# --------------------------------------------------------------------------


def visible_words(body: str) -> int:
    """Word count of what a reader sees.

    Markdown link targets aren't words on the page, so [text](url) counts
    as its text only. Otherwise adding citations would push a post over
    the limit for no reason a reader could see.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    text = re.sub(r"[#>*_`]", " ", text)
    return len(text.split())


def plain_text(body: str) -> str:
    """The prose, with markdown link targets and syntax taken out."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", body)
    return re.sub(r"[#>*_`]", " ", text)


def accusing_sentences(body: str) -> list:
    """Sentences where an accusing word sits next to a name.

    A capitalised word that isn't the first word of the sentence is treated
    as a proper noun. That catches plenty of innocent things. Good. The cost
    of a false positive is a rewrite; the cost of a false negative is a
    letter from a solicitor.
    """
    flagged = []
    for line in plain_text(body).split("\n"):
        for raw in re.split(r"(?<=[.!?])\s+", line):
            sentence = raw.strip()
            if not sentence:
                continue
            low = sentence.lower()
            words = [w for w in ACCUSATIONS if w in low]
            if not words:
                continue
            names = []
            for token in sentence.split()[1:]:
                token = token.strip(",;:.!?()[]\"'“”‘’")
                if re.fullmatch(r"[A-Z][a-zA-Z'’-]+", token):
                    names.append(token)
            if names:
                flagged.append((sentence, sorted(set(words)), sorted(set(names))))
    return flagged


# A number in the opening sentence turns a post into a briefing note. Years
# are exempt: "The council voted in 1996" is a scene, not a statistic.
STATISTIC = re.compile(
    r"[£$€]\s?\d|\d+\s*%|\bper cent\b|\b\d[\d,]{2,}\b"
    r"|\b\d+(?:\.\d+)?\s*(?:million|billion|thousand|k)\b",
    re.I,
)
YEAR = re.compile(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b")

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "had", "has", "have", "he", "her", "his", "i", "if", "in", "is",
    "it", "its", "of", "on", "or", "she", "so", "that", "the", "their",
    "them", "then", "there", "they", "this", "to", "was", "were", "what",
    "when", "which", "who", "will", "with", "you", "your", "not", "no",
    "do", "does", "did", "can", "could", "would", "should", "one", "all",
    "more", "most", "some", "any", "than", "into", "out", "up", "about",
    "we", "us", "our", "me", "my",
}


def first_sentence(body: str) -> str:
    text = plain_text(body).strip()
    return re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0] if text else ""


# The standard slow openings. None of them is a claim, so none of them can
# be argued with, so none of them is a reason to read the second sentence.
THROAT_CLEARING = re.compile(
    r"^(in|by|on|since|during)\s+(the\s+)?(19|20)\d\d\b"
    r"|^(last|this|next)\s+(week|month|year|spring|summer|autumn|winter|monday|tuesday|wednesday|thursday|friday)"
    r"|^there (is|are|was|were)\b"
    r"|^it (is|has|was) (often|long|widely|generally|commonly|become)\b"
    r"|^(every|most|many|some|few)\s+\w+\s+(know|knows|think|thinks|believe|believes|agree|agrees)\b"
    r"|^we all\b|^imagine\b|^picture\b|^consider\b"
    r"|^for (years|decades|centuries|a long time)\b"
    r"|^(recently|lately|nowadays|today|these days|increasingly)\b"
    r"|^(the|a|an) \w+ (of|for|in) \w+ (is|are) (a|an|the) \w+ (subject|question|topic|issue)\b",
    re.I,
)


def weak_opening(body: str) -> str:
    """The first sentence, if it is an introduction rather than a claim."""
    first = first_sentence(body).strip()
    if not first:
        return ""
    if THROAT_CLEARING.match(first):
        return first
    if len(first.split()) > 25:
        return first
    return ""


def opens_on_a_statistic(body: str) -> str:
    """The opening sentence, if it leads on a number. Empty string if not."""
    first = first_sentence(body)
    return first if STATISTIC.search(YEAR.sub(" ", first)) else ""


def recent_bodies(n: int = 5) -> list:
    """The prose of the last few published posts, front matter stripped."""
    out = []
    for f in sorted(POSTS.glob("*.md"), reverse=True)[:n]:
        text = f.read_text(encoding="utf-8")
        parts = text.split("---")
        out.append(parts[2] if len(parts) > 2 else text)
    return out


def _phrases(text: str, n: int = 3) -> set:
    """Every n-word run carrying at least two words that mean something."""
    words = re.findall(r"[a-z']+", plain_text(text).lower())
    grams = set()
    for i in range(len(words) - n + 1):
        gram = words[i : i + n]
        if sum(1 for w in gram if w not in STOPWORDS) >= 2:
            grams.add(" ".join(gram))
    return grams


QUOTED = re.compile(r"[\"\u201c\u2018][^\"\u201c\u201d\u2018\u2019]*[\"\u201d\u2019]")


def reused_phrases(body: str, previous: list, limit: int = 8) -> list:
    """Phrases this post shares with ones already published.

    Quoted material is exempt. A correction post has to quote the sentence
    it is correcting, and flagging that as self-repetition would make the
    one kind of post the brief insists on impossible to write.
    """
    if not previous:
        return []
    body = QUOTED.sub(" ", body)
    seen = set()
    for prev in previous:
        seen |= _phrases(prev)
    return sorted(_phrases(body) & seen)[:limit]


def reused_opening(body: str, previous: list) -> str:
    """The earlier opening this one is imitating, if any."""
    new = re.findall(r"[a-z']+", first_sentence(body).lower())[:4]
    if len(new) < 3:
        return ""
    for prev in previous:
        old = re.findall(r"[a-z']+", first_sentence(prev).lower())[:4]
        if old and new[:3] == old[:3]:
            return first_sentence(prev)
    return ""


def clean_voices(raw) -> list:
    """The voices block, reduced to fields the template can render."""
    out = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        if not isinstance(v, dict):
            continue
        thinker = str(v.get("thinker") or "").strip()
        # The template always prefixes "Imaginary". Strip it if WE wrote it
        # too, or the page says Imaginary Imaginary Karl Marx.
        thinker = re.sub(r"^(an?\s+)?imaginary\s+", "", thinker, flags=re.I)
        raw_kind = str(v.get("kind") or "").strip().lower()
        kind = raw_kind if raw_kind in ("practitioner", "human") else "bench"
        if kind == "practitioner":
            thinker = thinker.lower()
        if kind == "human":
            thinker = "human"
        argument = str(v.get("argument") or "").strip()
        if not thinker or not argument:
            continue
        out.append(
            {
                "thinker": thinker,
                "kind": kind,
                "lived": "" if kind == "practitioner" else str(v.get("lived") or "").strip(),
                "argument": argument,
                "quote": str(v.get("quote") or "").strip(),
                "quote_url": str(v.get("quote_url") or "").strip(),
            }
        )
    # Bench argues, practitioner corrects, human delivers the verdict. In
    # that order, always, because the verdict goes last.
    rank = {"bench": 0, "practitioner": 1, "human": 2}
    out.sort(key=lambda v: rank[v["kind"]])
    return out


HUMAN_MAX_WORDS = 30
POLITE = ("interesting", "thought-provoking", "well written", "good post",
          "nice piece", "compelling", "insightful", "great read", "well argued")


def check_human_verdict(said) -> list:
    said = str(said or "").strip()
    if not said:
        return ["No human verdict. Every post ends with a reader saying what "
                "they thought, in under thirty words."]
    failures = []
    n = len(said.split())
    if n > HUMAN_MAX_WORDS:
        failures.append(
            f"The human verdict runs to {n} words. The cap is "
            f"{HUMAN_MAX_WORDS} and the cap is the whole voice."
        )
    soft = [w for w in POLITE if w in said.lower()]
    if soft:
        failures.append(
            "The human verdict is being nice: " + ", ".join(f'"{w}"' for w in soft)
            + ". It is not there to encourage anybody."
        )
    return failures


def check_human(voices: list) -> list:
    """Somebody who has just read it, saying what they actually think."""
    humans = [v for v in voices if v["kind"] == "human"]
    if not humans:
        return ["No human voice. Every post ends with one: a short flat "
                "verdict from somebody who has just read it. Two sentences "
                "at the outside. No reasoning, no manners."]
    if len(humans) > 1:
        return ["More than one human voice. There is one reader and they "
                "speak once."]
    said = humans[0]["argument"]
    n = len(said.split())
    failures = []
    if n > HUMAN_MAX_WORDS:
        failures.append(
            f"The human runs to {n} words. The cap is {HUMAN_MAX_WORDS} and "
            "the cap is the whole voice. If it needs a paragraph it is not a "
            "verdict, it is another opinion, and the post already has plenty."
        )
    soft = [w for w in POLITE if w in said.lower()]
    if soft:
        failures.append(
            "The human is being nice: " + ", ".join(f'"{w}"' for w in soft)
            + ". This voice is not there to be encouraging. If the post is "
            "good it can say so in three words and still sound unimpressed."
        )
    return failures


def check_voices(voices: list, returned_urls: set) -> list:
    """A made-up quotation from a dead thinker is a made-up source.

    The argument field is WE's own words and may not contain quotation
    marks at all. Anything in quotes goes in the quote field, and only
    with a link a search actually returned.
    """
    failures = []
    for v in voices:
        who = v["thinker"]

        if re.search(r'["“”]', v["argument"]):
            failures.append(
                f"The {who} voice has quotation marks in its argument. That "
                "field is your own words about how the argument runs. If you "
                "want to quote the person, search for the real words and put "
                "them in the quote field with a link."
            )

        # The bench may never be ventriloquised: those were real people and
        # they did not say this. A practitioner is invented outright, says so
        # on the page, and the first person is the whole value of it.
        if v.get("kind") not in ("practitioner", "human") and re.search(
            r"\bI\b|\bmy\b|\bmine\b", v["argument"]
        ):
            failures.append(
                f"The {who} voice is written in the first person. You are not "
                "speaking as them and the post must never look like you are. "
                "Write it as a description of the argument."
            )

        surname = who.split()[-1]
        m = None if v.get("kind") in ("practitioner", "human") else re.search(
            rf"\b{re.escape(surname)}\b", v["argument"], re.I
        )
        if m:
            # Wide enough to see "Imaginary" in front of a two-word surname
            # like Spärck Jones or de Beauvoir.
            lead = v["argument"][max(0, m.start() - 30) : m.start()].lower()
            if "imaginary" not in lead:
                failures.append(
                    f"The {who} voice names {surname} without calling him or "
                    "her imaginary. The first mention in the argument is "
                    f'"imaginary {surname}". After that you can use the bare '
                    "name and the prose stays readable."
                )

        quote, url = v["quote"], v["quote_url"]
        if quote and not url:
            failures.append(
                f"The {who} voice quotes words with no link. Every quotation "
                "needs a source a search returned. No link, no quote: cut it "
                "and describe the argument instead."
            )
        elif quote and url and url not in returned_urls:
            failures.append(
                f"The {who} voice quotes words sourced to {url}, which no "
                "search returned. Don't reconstruct a citation from memory. "
                "Search for it, or cut the quotation."
            )

    return failures


DATED = re.compile(
    r"\b20[2-9]\d\b|\bwithin (?:the next )?\w+ (?:months?|years?)\b"
    r"|\bby (?:the end of|mid|early|late)\b|\bnext (?:year|decade)\b",
    re.I,
)


def numbers_in(text: str) -> set:
    """Digit strings, commas stripped, so 2,313 and 2313 are the same number."""
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text or "")}


def check_derived_number(derived, body: str, returned_urls: set) -> list:
    """One number in every post that appears in no source.

    Two published figures put next to each other is the cheapest original
    thought available and almost nobody bothers. It also cannot be done by
    reading. You have to stop and work something out.
    """
    if not isinstance(derived, dict):
        return ["No derived number. Every post works out one figure that "
                "appears in none of the sources, from figures that do. Two "
                "published numbers next to each other is the whole trick."]

    figure = str(derived.get("figure") or "").strip()
    working = str(derived.get("working") or "").strip()
    srcs = [str(u).strip() for u in (derived.get("sources") or []) if str(u).strip()]
    failures = []

    if not figure or not numbers_in(figure):
        failures.append(
            "The derived figure has no number in it. It has to be a figure: a "
            "ratio, a share, a rate, a per head, a multiple, a difference."
        )
    if len(numbers_in(working)) < 2:
        failures.append(
            f'The working does not show two published numbers going in: '
            f'"{working}" Show the arithmetic. A reader has to be able to '
            "check it on the back of an envelope."
        )
    if not srcs:
        failures.append("The derived number cites no sources for its inputs.")
    else:
        ghosts = [u for u in srcs if u not in returned_urls]
        if ghosts:
            failures.append(
                "The derived number takes inputs from " + ", ".join(ghosts)
                + ", which no search returned. Derive it from numbers you "
                "actually found."
            )
    if figure and numbers_in(figure) and not (numbers_in(figure) & numbers_in(body)):
        failures.append(
            f'You worked out "{figure}" and then left it out of the post. '
            "The whole point is that the reader sees it."
        )
    return failures


def check_refutation(refutation) -> list:
    """One search aimed at killing your own argument, before you write it."""
    if not isinstance(refutation, dict):
        return ["No refutation search. Before writing, search once for the "
                "strongest case that your argument is wrong, and report what "
                "came back."]
    searched = str(refutation.get("searched") or "").strip()
    did = str(refutation.get("what_it_did") or "").strip()
    failures = []
    if len(searched.split()) < 3:
        failures.append(
            f'The refutation search is not a real search: "{searched}" Write '
            "the query you would run if you were trying to prove yourself "
            "wrong, and run it."
        )
    if not did:
        failures.append(
            "You didn't say what the refutation search did to the post. If it "
            "came back empty, say that. If it came back full, the post should "
            "look different, and you should say how."
        )
    return failures


def check_prediction(prediction: str) -> list:
    """A claim about the future that cannot be checked is not a prediction."""
    prediction = (prediction or "").strip()
    if not prediction:
        return [
            "No prediction. Every post says what happens next, in a form that "
            "could turn out wrong. Name a thing, a time and a mechanism."
        ]
    if not DATED.search(prediction):
        return [
            f'The prediction has no date in it: "{prediction}" Give it a year '
            "or a window with an end, or nobody can ever say you were wrong."
        ]
    hedges = [h for h in ("or something like it", "in some form", "or similar",
                          "to some extent", "in one way or another") if h in prediction.lower()]
    if hedges:
        return [
            "The prediction is hedged into safety with "
            + ", ".join(f'"{h}"' for h in hedges)
            + ". Take the hedge out and say the thing."
        ]
    return []


def check_thesis_update(update) -> list:
    """Either you moved, and said what moved you, or you said what would."""
    if not isinstance(update, dict):
        return ["No thesis_update. Every run either changes the thesis or says "
                "what would change it."]
    if update.get("changed"):
        if not str(update.get("what") or "").strip():
            return ["The thesis changed but you didn't say what moved it. The "
                    "cause is the interesting part, not the conclusion."]
        return []
    if not str(update.get("would_change_it") or "").strip():
        return ["The thesis didn't change and you didn't say what would. A "
                "thesis with no stated way of being wrong is a mood."]
    return []


def record_thesis(update, date: str, title: str) -> None:
    """Add to the top of thesis.md. Never overwrite what's underneath."""
    if not isinstance(update, dict) or not update.get("changed"):
        return
    existing = THESIS.read_text(encoding="utf-8") if THESIS.exists() else "# The thesis\n"
    head, _, rest = existing.partition("\n---\n")
    entry = (f"\n---\n\n## Revised {date}, after \"{title}\"\n\n"
             f"{str(update.get('what')).strip()}\n")
    THESIS.write_text(head + entry + "\n---\n" + rest, encoding="utf-8")


def record_prediction(prediction: str, title: str, date: str, url: str) -> None:
    header = ("# Predictions\n\nEvery claim WE has made about what happens next, "
              "with the post that made it. Newest first.\n")
    entry = f"\n## {date}\n\n{prediction.strip()}\n\nFrom [{title}]({url})\n"
    existing = PREDICTIONS.read_text(encoding="utf-8") if PREDICTIONS.exists() else ""
    body = existing[len(header):] if existing.startswith(header) else existing
    PREDICTIONS.write_text(header + entry + body, encoding="utf-8")


def professions_mentioned(body: str) -> list:
    low = plain_text(body).lower()
    return [j for j in PROFESSIONS if re.search(rf"\b{re.escape(j)}s?\b", low)]


def check_practitioner(body: str, voices: list) -> list:
    """If the post leans on a job, somebody who does it gets a reply."""
    jobs = professions_mentioned(body)
    if not jobs:
        return []
    if any(v.get("kind") == "practitioner" for v in voices):
        return []
    named = ", ".join(jobs[:4])
    return [
        f"The post talks about work done by people ({named}) and none of them "
        "answers back. Add a short practitioner voice: an imaginary "
        f"{jobs[0]}, a few sentences, on what the post gets wrong about the "
        "actual job. Not a famous name. Somebody who does it."
    ]


def sentences(body: str) -> list:
    out = []
    for line in plain_text(body).split("\n"):
        for raw in re.split(r"(?<=[.!?])\s+", line):
            s = raw.strip()
            if s:
                out.append(s)
    return out


def check_rhythm(body: str) -> list:
    """All sentences the same length is a hedge trimmed flat."""
    lengths = [len(s.split()) for s in sentences(body)]
    if len(lengths) < 4:
        return []
    failures = []
    if min(lengths) > 5:
        failures.append(
            f"Nothing short anywhere. The briefest sentence in the post runs "
            f"to {min(lengths)} words. Every post needs at least one under "
            "five. Short. Like that."
        )
    if max(lengths) - min(lengths) < 12:
        failures.append(
            f"Every sentence is roughly the same length, {min(lengths)} to "
            f"{max(lengths)} words. That is a hedge trimmed flat, and it "
            "reads like one however right it is. Break some. Let one run."
        )
    return failures


def check_verbs(body: str) -> list:
    """How much of the post is things being, rather than things happening."""
    ss = sentences(body)
    if len(ss) < 6:
        return []
    on_is = sum(1 for s in ss if COPULA.search(s))
    pct = round(100 * on_is / len(ss))
    if pct <= COPULA_CEILING:
        return []
    return [
        f"{pct} per cent of the sentences run on is, are, was or were. The "
        f"ceiling is {COPULA_CEILING} and the voice you are aiming at sits "
        "near thirty. A sentence built on is describes a state and nothing "
        "happens in it. Subject, verb, object. Somebody does something to "
        "something. Rewrite half of them with a verb that moves."
    ]


def check_style(body: str) -> list:
    low = plain_text(body).lower()
    failures = []
    posts = [s for s in SIGNPOSTS if s in low]
    if posts:
        failures.append(
            "Signposting: " + ", ".join(f'"{s}"' for s in posts)
            + ". Announcing a paragraph is not writing it. Delete the "
            "announcement and start with the thing itself. The reader worked "
            "out that a post has parts."
        )
    hit = [p for p in DEFLATING if p in low]
    if hit:
        failures.append(
            "Announcing your own fairness: " + ", ".join(f'"{h}"' for h in hit)
            + ". Keep the concession, cut the trumpet. Make the other case in "
            "its own voice at full speed and let the reader notice you were "
            "fair by seeing you be fair."
        )
    soft = [h for h in HEDGES if h in low]
    if soft:
        failures.append(
            "Hedging: " + ", ".join(f'"{h}"' for h in soft)
            + ". Each one is an escape route bought with the reader's "
            "attention. Say the strong version. If it turns out wrong, that "
            "is a post, and a better one."
        )

    dead = [d for d in DEAD_IMAGES if d in low]
    if dead:
        failures.append(
            "Dead metaphors: " + ", ".join(f'"{d}"' for d in dead)
            + ". These are abstractions in a picture's coat. Find a real image "
            "or use a plain word."
        )
    return failures


def check_post(body: str, previous: list = None) -> list:
    """Every way this post breaks the brief. Empty list means it's clean."""
    failures = []

    words = visible_words(body)
    if words > WORD_LIMIT:
        failures.append(
            f"Too long: {words} words. The ceiling is {WORD_LIMIT}. "
            "You've probably got two ideas in there. Keep one, save the "
            "other for the agenda."
        )

    if EM_DASH in body:
        n = body.count(EM_DASH)
        failures.append(
            f"Em dash used {n} time{'s' if n > 1 else ''}. The brief bans it "
            "outright. Every one of them is two sentences. Split them."
        )

    low = body.lower()
    hits = sorted({w for w in BANNED if w in low})
    if hits:
        failures.append(
            "Banned words used: " + ", ".join(hits) + ". These are forbidden "
            "in any form. Say \"not enough of it\" instead of scarcity, "
            "\"leftover\" or \"hangover\" instead of artefact. Rewrite the "
            "sentences, don't swap the word."
        )

    if body.rstrip().endswith("?"):
        failures.append(
            "Ends on a question mark. The brief says never end on a question. "
            "Write the last line yourself and make it worth remembering."
        )

    slow = weak_opening(body)
    if slow:
        words = len(slow.split())
        why = ("It runs to %d words, which is an argument rather than an "
               "assertion." % words) if words > 25 else (
               "It sets a scene instead of claiming something.")
        failures.append(
            f'Weak opening: "{slow}" {why} Open on a short, surprising claim '
            "a reader could argue with. If nobody could say no it isn't, it "
            "is an introduction, and nobody reads those."
        )

    opener = opens_on_a_statistic(body)
    if opener:
        failures.append(
            f'Opens on a statistic: "{opener}" The brief says never. A number '
            "is the evidence, not the hook. Open on something happening, a "
            "rule in its own words, or a plain sentence that makes the next "
            "one necessary. Move the number to the second or third paragraph."
        )

    previous = previous or []

    echo = reused_opening(body, previous)
    if echo:
        failures.append(
            "Opens the same way as an earlier post. That one began: "
            f'"{echo}" Find a different way in.'
        )

    reused = reused_phrases(body, previous)
    if reused:
        failures.append(
            "Phrases lifted from your own earlier posts: "
            + "; ".join(f'"{p}"' for p in reused)
            + ". A construction you liked once is a tic the second time. "
            "Say it differently, or say something else."
        )

    failures += check_rhythm(body)
    failures += check_verbs(body)
    failures += check_style(body)

    risky = accusing_sentences(body)
    if risky:
        quoted = "\n".join(
            f'      "{s}"\n        [{", ".join(w)} + {", ".join(n)}]'
            for s, w, n in risky
        )
        failures.append(
            "Possible accusation against a named party. An accusing word is in "
            "the same sentence as a name here:\n" + quoted + "\n"
            "    Attack the rule, never whoever benefits from it. Cut the name, "
            "cut the accusation, or say only what a source you have linked says "
            "that person or company said or did. This check over-triggers on "
            "purpose. If it's a false alarm, reword so the name and the word "
            "aren't in the same sentence."
        )

    return failures


def rewrite_request(failures: list, sources: list) -> str:
    """Hand the failures back and ask for the post again."""
    listed = "\n".join(f"{i}. {f}" for i, f in enumerate(failures, 1))
    return f"""That post breaks the brief. Here's what's wrong:

{listed}

Write it again. Not a patch, not a find-and-replace on the sentences that
broke. Rewrite the post so the problems don't exist. The idea can stay if
it's a good one.

{sources_note(sources)}

Return the same JSON object, complete, with every field filled in. No
preamble, no fences."""


def sources_note(sources: list) -> str:
    if not sources:
        return "You have web search. Use it if you need to check anything."
    listed = "\n".join(f"- {s['title']}: {s['url']}" for s in sources)
    return (
        "These are the pages your searches actually returned. Link claims to "
        "them inline in the body, and list the ones you used in "
        '"sources":\n\n' + listed
    )



# --------------------------------------------------------------------------
# the critic
# --------------------------------------------------------------------------

CRITIC_SCHEMA = """{
  "dull": true or false,
  "dull_because": "one sentence, empty if not dull",
  "timid": true or false,
  "timid_because": "where the post stopped one step short of what its own argument implies, or empty",
  "nothing_new": true or false,
  "nothing_new_because": "what the post's central claim is, where it is already commonplace, and what a reader gets here that they could not get from a search. empty if it is genuinely new",
  "flat_open": true or false,
  "flat_open_because": "the first sentence, and why nobody would argue with it. empty if it lands",
  "same_post": true or false,
  "same_post_because": "which earlier post, and what shape they share. empty if not",
  "bad_sources": ["for each weak citation: the claim, the source, why it will not carry it"],
  "hateful": ["anything racist, misogynistic or hateful, in the post or in a voice. usually empty"],
  "idle_voices": ["any voice that agrees with the post and is doing no work"],
  "unanswered": "the strongest objection the post does not deal with, or empty",
  "human_verdict": "you, as somebody who just read it, in under 30 words. blunt. no reasoning, no manners, never the word interesting",
  "human_fix": "the single change that would most improve it, in one line. empty if there is nothing worth another draft",
  "notes": ["things worth remembering next time, one line each"]
}"""


def critique(client, post: dict, voices: list, previous: list, brief: str) -> dict:
    """A second call, with no memory of having written the thing.

    Everything here is a judgement no regex can make: is it dull, is it the
    same post again, is that source any good, is anything in it vile. The
    critic never rewrites. It reports, and the writer gets told.
    """
    voice_text = "\n\n".join(
        f"Imaginary {v['thinker']}: {v['argument']}" for v in voices
    ) or "(no voices in this post)"
    prior = "\n\n---\n\n".join(p.strip()[:1200] for p in previous) or "(nothing published yet)"

    prompt = f"""You are reading a draft for a site called WE. You did not write it and you owe it nothing.

Your job is to find what is wrong with it. Not to improve it, not to be encouraging, not to summarise it. Someone else will do the rewriting. You say what is wrong.

Here is the standing brief the draft is written to.

{brief}

---

Here are the last few things the site published.

{prior}

---

Here is today's draft.

TITLE: {post.get('title', '')}

{post.get('body', '')}

VOICES:

{voice_text}

---

Judge it on the things a regex cannot see.

Is it dull? Not imperfect, dull. Would anyone who is not paid to be here reach the end. Reserve dull for a piece with no reason to exist, and if that is the honest answer, say it.

Then look specifically for the things that make prose lifeless even when the argument is good. Is there a single real image anywhere, or is it abstract nouns end to end. Is there one line that is actually funny. Does the writer appear to want anything, or is the whole thing delivered at the same polite temperature from start to finish. Say which of these is missing, by name.

Where does the post stop short? Take its own argument and push it one more step than the writer did. If the next step follows from what has been written and the post declines to take it, that is timidity and it is the most common way a good piece ends up forgettable. Say what the unwritten step was. If the post already goes all the way, say so.

Now the hardest question and the one that matters most. Is there anything in this post that a reader could not have got from the first page of a search on the subject?

Work out what the central claim is, in one sentence, and then search for it. If the internet is already full of that claim, the post is a summary however well written it is, and you should say so and say where the claim already lives. Clear summaries are free now. Producing one is not an achievement.

Be precise about what counts as new. A fact the reader didn't know is not new; somebody knew it. New means a connection nobody had drawn, an agreed thing that turns out to be wrong, an exception nobody explains, a second order effect nobody followed, or the view from somebody who never gets asked. If the post has one of those, say which. If it has none, say so plainly.

Read only the first sentence and stop. Would anybody argue with it? A reader
has to be able to think "no it isn't" and keep reading to find out. If the
first sentence is a scene, a date, a summary of the subject or a statement
nobody could dispute, it is flat, and say so. Being well written does not
save it.

Is it the same post as one of the earlier ones? Same shape, not same words. Opens the same way, concedes in the same place, lands the same closing move, points the core question at the same kind of target.

For every vivid detail in the post, check three things separately: does it happen, is it common, does it work. A source establishing the first does not establish the other two. If the post treats a real but rare or ineffective thing as though it were widespread or effective, say so, because that is the most common way an honest writer misleads.

Are the sources any good? Take each claim that carries a citation and ask what the source actually is. A press release is not evidence for a global statistic. A company blog is not evidence for a market forecast that company sells into. A firm selling the cure is not evidence for the rate of the disease. If two named organisations disagree by an order of magnitude and the post quotes only one, that is a choice of conclusion dressed as a fact.

If the whole post rests on a single article, say that too. Search if you need to check what a source is. Name the claim, the source, and why it will not carry the weight.

Is anything in it racist, misogynistic or hateful, in the post or in any of the voices. A dead thinker's name is not a defence. This is usually empty and you should not invent something to fill it.

Do any of the voices agree with the post? A voice that agrees is doing no work.

What is the strongest objection the post does not deal with.

Last, and separately from everything above: stop being a critic for a moment and be a reader. You have just finished the piece. What do you actually think, in under thirty words, said the way a person says it to a friend rather than the way a reviewer writes it down. No preamble, no compliment sandwich, and never the word interesting.

Then say the one change that would most improve the post, in a line. If it genuinely needs no further draft, leave that empty and say so by leaving it empty.

Return ONLY this JSON, no preamble, no fences:

{CRITIC_SCHEMA}"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        tools=CRITIC_TOOLS,
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_json(text_blocks(resp), require=("dull", "same_post"))


def critic_failures(verdict: dict) -> list:
    """The parts of the critic's verdict that stop a post going out."""
    failures = []

    for item in verdict.get("hateful") or []:
        failures.append(
            f"The critic found something hateful: {item} Cut it. This one is "
            "not a judgement call and it is not negotiable."
        )

    if verdict.get("timid"):
        failures.append(
            "The critic says it stops short: "
            f"{verdict.get('timid_because') or '(no reason given)'} "
            "Take the step. Then check whether it was actually mad."
        )

    if verdict.get("nothing_new"):
        failures.append(
            "The critic can't find anything new in it: "
            f"{verdict.get('nothing_new_because') or '(no reason given)'} "
            "A summary is not a post. Find the connection nobody has drawn, "
            "the agreed thing that is wrong, the exception nobody explains, "
            "or the person nobody asked. Then write that instead."
        )

    if verdict.get("flat_open"):
        failures.append(
            "The critic says the opening is flat: "
            f"{verdict.get('flat_open_because') or '(no reason given)'} "
            "Find the surprising true thing the post knows and lead with it."
        )

    if verdict.get("dull"):
        failures.append(
            "The critic says it's dull: "
            f"{verdict.get('dull_because') or '(no reason given)'} "
            "Don't attach a voice saying it's dull. Rewrite it, or write a "
            "different post."
        )

    if verdict.get("same_post"):
        failures.append(
            "The critic says this is a post you have already written: "
            f"{verdict.get('same_post_because') or '(no reason given)'} "
            "Change the shape or change the subject."
        )

    for item in verdict.get("bad_sources") or []:
        failures.append(
            f"The critic doesn't accept a source: {item} Find something that "
            "carries the claim, or cut the claim."
        )

    fix = str(verdict.get("human_fix") or "").strip()
    if fix:
        failures.append(
            f"The reader would change one thing: {fix} Do that, then hand it "
            "back. Whatever they still object to after this can be published "
            "with their objection attached. This one gets fixed first."
        )

    failures += check_human_verdict(verdict.get("human_verdict"))

    for item in verdict.get("idle_voices") or []:
        failures.append(
            f"A voice is doing no work: {item} A jury of people who agree "
            "with you is not a jury. Cut it or replace it with someone who "
            "would argue."
        )

    return failures


def record_critique(verdict: dict, title: str, date: str, kept: int = 20) -> None:
    """Append the critic's notes to a file WE reads and cannot write to."""
    lines = [f"## {date} — {title}", ""]
    if verdict.get("unanswered"):
        lines.append(f"- Unanswered objection: {verdict['unanswered']}")
    for note in verdict.get("notes") or []:
        lines.append(f"- {note}")
    if len(lines) == 2:
        lines.append("- Nothing to add.")
    entry = "\n".join(lines) + "\n"

    existing = CRITIC.read_text(encoding="utf-8") if CRITIC.exists() else ""
    header = "# What the critic said\n\nWritten after each post by a reader that did not write it. WE cannot edit this file.\n"
    body = existing.split("\n", 3)[-1] if existing.startswith("# What the critic said") else existing
    entries = [e for e in ("\n" + body).split("\n## ") if e.strip()]
    entries = [entry] + [("## " + e).rstrip() + "\n" for e in entries]
    CRITIC.write_text(header + "\n" + "\n".join(entries[:kept]), encoding="utf-8")


# --------------------------------------------------------------------------
# the prompt
# --------------------------------------------------------------------------


def current_thesis() -> str:
    if not THESIS.exists():
        return "(no thesis yet: write version 0 in this run)"
    return THESIS.read_text(encoding="utf-8").strip()


def past_predictions() -> str:
    if not PREDICTIONS.exists():
        return "(nothing predicted yet)"
    return PREDICTIONS.read_text(encoding="utf-8").strip() or "(nothing predicted yet)"


def critic_notes() -> str:
    if not CRITIC.exists():
        return "(no critic notes yet)"
    return CRITIC.read_text(encoding="utf-8").strip() or "(no critic notes yet)"


def build_prompt() -> str:
    return f"""{BRIEF.read_text(encoding="utf-8")}

---

## Your running agenda

This is your own file. You wrote most of it. It records what you're
chasing, what you've abandoned, and what evidence has gone against you.

{AGENDA.read_text(encoding="utf-8")}

---

## What the critic said about earlier posts

This file is written by a reader that did not write the posts. You cannot
edit it. Read it before you start.

{critic_notes()}

---

## Your thesis as it currently stands

{current_thesis()}

---

## What you have already predicted

You will be judged on these. Don't repeat one, and if you now think an
earlier one was wrong, say so in the post rather than quietly dropping it.

{past_predictions()}

---

## Already published

{recent_posts()}

---

## Now

Write today's post. Pick from your agenda, or follow something better if
you've found it. You decide, and if you depart from the agenda, say why
in the agenda update.

You have web search. Use it.

Search for every number, date, study, name, quote and event before you
put it in the post. Not "search if you feel unsure". Search every time.
Your memory of a fact is not a source.

If a search doesn't confirm a claim, cut the claim. Don't soften it,
don't hedge it, don't reach for a near-enough number. Make the point
without it. If the point can't survive losing an unverified fact, it was
never the point.

## Sources

Link your evidence inline, in the body, as ordinary markdown links:
`[the Institute for Fiscal Studies found](https://example.org/page)`.
A reader should be able to click the claim and land on the thing that
backs it. Don't dump a wall of links at the end.

Then list every source you actually used in the "sources" field. Only the
ones you used. A page you searched and ignored is not a source. Never
write "studies show".

Only use URLs your searches actually returned. Don't reconstruct a link
from memory, and don't guess at one that looks right.

## Before you answer, check your own post

- Under {WORD_LIMIT} words.
- No em dash anywhere. Not one.
- No "artefact", no "scarcity", no "scarce", in any form.
- Doesn't end on a question mark.
- Contains one thing a reader could not have got from a search. If you
  can't say in a sentence what is new in it, start again.
- Works out one number that is in none of your sources, shows the sum,
  and puts the answer in the post.
- Ran one search whose only purpose was to prove the argument wrong, and
  says what came back.
- Opens on a short surprising claim somebody could argue with, and the
  post earns it.
- Has one sentence under five words, one real image, and one line that
  risks being funny.
- Fewer than half the sentences run on is, are, was or were. Somebody
  does something to something.
- Announces nothing. No "here is what happened", no "the interesting
  question is". Start with the thing.
- Uses one polemical move on purpose, and not the one you used last time.
- Makes the other case without announcing that it is being fair.
- Says the strong version. No hedges bought with the reader's attention,
  and it doesn't stop one step short of where its own argument goes.
- Says what happens next, with a date, in a form that could be wrong.
  Not hedged into safety.
- Uses history as evidence, never as the subject.
- Came from a vantage point somebody else isn't already standing at.
- If it talks about a job, somebody who does that job answers back.
- Do not write the human voice. A reader who did not write the post adds
  it afterwards, and you will be asked to fix whatever they object to
  before it is published.
- Says whether the thesis moved, and if not, what would move it.
- Doesn't open on a statistic. No price, percentage or count in the
  first sentence.
- Doesn't reuse an opening move or a turn of phrase from an earlier
  post. Read the last five before you start.
- No accusing word anywhere near a named person or company. Attack the
  rule, never whoever benefits from it. This one is a legal matter, not a
  style note.
- Nothing racist, misogynistic or hateful about any group, anywhere in
  the post or in any voice. An imaginary thinker saying it is you saying
  it with a dead person's name on it. No code checks this one. You do.

If it fails any of those, fix it before you reply. You get two more goes
after this, and then it publishes as written, so it's on you.

Do the searching first. Then, in your final message, return ONLY valid
JSON, in one piece, no preamble, no markdown fences:

{{
  "title": "the post title",
  "body": "the full post in markdown, under {WORD_LIMIT} words, no title heading",
  "short_version": "under 280 characters, must survive without the post",
  "prediction": "what happens next, with a date or a window, in a form that can be shown to be wrong",
  "derived_number": {{"figure": "one number that appears in none of your sources, worked out from ones that do",
                     "working": "the arithmetic, shown, from which published figures",
                     "sources": ["the urls the input numbers came from"]}},
  "refutation": {{"searched": "the query you ran to find the strongest case that you are wrong",
                 "found": "the best counter-evidence it returned, or empty if it came back with nothing",
                 "what_it_did": "how that changed the post"}},
  "technique": "which polemical move you used this time, one of: reversal, refrain, their own words, register collision, straight face, concrete swap, the list that argues, the sentence that turns",
  "jury_notes": "what three of the bench each noticed that the others could not see. a short paragraph. this is working, not prose",
  "thesis_update": {{"changed": true or false,
                    "what": "what changed in the thesis and what moved it, or empty",
                    "would_change_it": "if nothing changed, what evidence would"}},
  "sources": [{{"title": "what it is", "url": "https://..."}}],
  "voices": [{{"thinker": "Karl Marx", "kind": "bench", "lived": "1818 to 1883",
              "argument": "how the argument runs, in your words, no quote marks, never first person",
              "quote": "only real searched words, or empty",
              "quote_url": "the link a search returned, or empty"}},
             {{"kind": "practitioner", "thinker": "lawyer",
              "argument": "a few sentences from somebody who does the job, on what the post gets wrong about it"}},
             ],
  (a human voice is added afterwards by a reader who did not write the post: do not write one yourself)
  "agenda_update": "the complete new contents of agenda.md, in markdown"
}}"""


# --------------------------------------------------------------------------
# writing it out
# --------------------------------------------------------------------------


def yaml_str(value: str) -> str:
    """A YAML double-quoted scalar. JSON's escaping is valid YAML, but keep
    the accents as themselves: these files are meant to be read."""
    return json.dumps(value, ensure_ascii=False)


def front_matter(title: str, now: datetime, sources: list, voices: list) -> str:
    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"date: {now.isoformat()}",
        "layout: post.njk",
    ]
    if sources:
        lines.append("sources:")
        for s in sources:
            # json.dumps gives a double-quoted scalar YAML reads correctly.
            lines.append(f"  - title: {yaml_str(s['title'])}")
            lines.append(f"    url: {yaml_str(s['url'])}")
    if voices:
        lines.append("voices:")
        for v in voices:
            lines.append(f"  - thinker: {yaml_str(v['thinker'])}")
            lines.append(f"    kind: {yaml_str(v['kind'])}")
            lines.append(f"    lived: {yaml_str(v['lived'])}")
            lines.append(f"    argument: {yaml_str(v['argument'])}")
            if v["quote"] and v["quote_url"]:
                lines.append(f"    quote: {yaml_str(v['quote'])}")
                lines.append(f"    quote_url: {yaml_str(v['quote_url'])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> int:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": build_prompt()}]
    searched = []
    searches = 0
    post = None
    failures = []
    # Read once, before anything is written, so the new post is never
    # compared against itself.
    published = recent_bodies()

    for attempt in range(MAX_RETRIES + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            tools=TOOLS,
            messages=messages,
        )
        searches += sum(
            1 for b in resp.content if getattr(b, "type", None) == "server_tool_use"
        )
        merge_sources(searched, harvest_sources(resp))
        post = extract_json(text_blocks(resp))
        voices = clean_voices(post.get("voices"))
        failures = check_post(post["body"], published)
        failures += check_voices(voices, {s["url"] for s in searched})
        failures += check_practitioner(post["body"], voices)
        failures += check_prediction(post.get("prediction"))
        failures += check_derived_number(
            post.get("derived_number"), post["body"], {s["url"] for s in searched}
        )
        failures += check_refutation(post.get("refutation"))
        failures += check_thesis_update(post.get("thesis_update"))

        # Only worth paying for a critic once the cheap checks are clean.
        verdict = {}
        if not failures:
            try:
                verdict = critique(client, post, voices, published, BRIEF.read_text(encoding="utf-8"))
                failures += critic_failures(verdict)
            except Exception as exc:  # a critic that breaks must not block a post
                print(f"Critic failed, publishing without it: {exc}")

        if not failures:
            if attempt:
                print(f"Brief checks passed on rewrite {attempt}.")
            break

        print(f"Attempt {attempt + 1} failed the brief:")
        for f in failures:
            print(f"  - {f}")

        if attempt == MAX_RETRIES:
            break

        # Hand the whole exchange back, search blocks included, so the
        # rewrite still has the evidence in front of it.
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": rewrite_request(failures, searched)})

    # The reader's verdict goes on the page, written by the critic rather
    # than by the writer. Whatever survived two rewrites gets published with
    # the objection still attached.
    if verdict.get("human_verdict"):
        voices = clean_voices(
            [dict(v) for v in voices]
            + [{"kind": "human", "argument": verdict["human_verdict"]}]
        )

    sources = clean_sources(post.get("sources"))

    # A cited url that no search returned is the one thing that can't be
    # allowed to pass quietly. Say so; don't silently drop it.
    returned = {s["url"] for s in searched}
    unverified = [s for s in sources if s["url"] not in returned]

    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    slug = slugify(post["title"])
    path = POSTS / f"{date}-{slug}.md"

    # Front matter, then the body exactly as the model wrote it. No edits.
    path.write_text(
        front_matter(post["title"], now, sources, voices)
        + "\n"
        + post["body"].strip()
        + "\n",
        encoding="utf-8",
    )

    AGENDA.write_text(post["agenda_update"].strip() + "\n", encoding="utf-8")

    LATEST.write_text(
        json.dumps(
            {
                "title": post["title"],
                "short_version": post["short_version"][:280],
                "url": f"{SITE}/posts/{date}-{slug}/",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if verdict:
        record_critique(verdict, post["title"], date)
    record_prediction(post.get("prediction", ""), post["title"], date,
                      f"{SITE}/posts/{date}-{slug}/")
    record_thesis(post.get("thesis_update"), date, post["title"])

    print(f"Wrote {path.name} ({searches} searches, {len(sources)} sources cited)")
    if verdict.get("unanswered"):
        print(f"Critic's unanswered objection: {verdict['unanswered']}")

    if unverified:
        print("!" * 60)
        print("SOURCES NOT RETURNED BY ANY SEARCH, CHECK THESE BY HAND:")
        for s in unverified:
            print(f"  - {s['title']}: {s['url']}")
        print("!" * 60)

    if failures:
        print("!" * 60)
        print(f"PUBLISHED ANYWAY AFTER {MAX_RETRIES} REWRITES. STILL BREAKS THE BRIEF:")
        for f in failures:
            print(f"  - {f}")
        print(f"  file: {path}")
        print("!" * 60)

    # Exit 0 either way, on purpose. A non-zero exit would stop the workflow
    # before the commit step and the post would never publish, which isn't
    # what "save it anyway" means. So flag it where it can still be seen.
    flag_in_ci(failures, unverified, path)
    return 0


def flag_in_ci(failures: list, unverified: list, path: pathlib.Path) -> None:
    """Put any misses on the Actions run page, without failing the run."""
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary or not (failures or unverified):
        return
    lines = [f"### WE published `{path.name}` with problems", ""]
    for f in failures:
        lines.append(f"- **brief:** {f}")
    for s in unverified:
        lines.append(f"- **unverified source:** [{s['title']}]({s['url']})")
    with open(summary, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
