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
# What the person running WE has said about the work, kept from run to run.
# The human voice on a post dies with that post. This does not. WE reads it
# every run and cannot edit it, same as the critic.
NOTES = ROOT / "agent" / "notes.md"
# Every prediction WE has made, with the date it comes due. Nothing scores
# them yet. The point for now is that they exist somewhere they cannot be
# quietly forgotten.
PREDICTIONS = ROOT / "agent" / "predictions.json"
# WE's developing account of what is happening. Rewritten by WE each run,
# but only by adding to the top: the old versions stay underneath.
THESIS = ROOT / "agent" / "thesis.md"
# How the site describes itself. Same rule as the thesis: WE revises it by
# adding to the top, and every version it has given stays underneath. A
# description that can be quietly rewritten is not a promise, it is a mood.
ABOUT = ROOT / "src" / "about.md"
ABOUT_MARK = "<!-- revisions -->"
# Posts stopped by the defamation gate. Never committed, never built,
# never announced. Deliberately outside git: a public repository is
# publication in English law, so a draft held for a reputation risk must
# not be pushed to one. On a CI runner this directory dies with the
# runner and only the reasons reach the run summary. Run the agent
# locally and the draft survives here for a human to read.
HELD = ROOT / "agent" / "held"

MODEL = "claude-sonnet-4-6"
# 8000 was not enough. The model narrates through its searches before it
# writes anything, and a run that thinks hard about a hard post hits the
# ceiling mid-sentence and returns no JSON at all. Nothing is salvageable
# when that happens, so the ceiling should sit well above the worst case.
MAX_TOKENS = 16000
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
    "civil servant", "reporter", "press officer", "councillor",
    "caseworker", "investigator", "official",
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

# Answers to "who does this happen to" that are not answers.
NOBODIES = (
    "society", "everyone", "people", "the public", "stakeholders",
    "the industry", "policymakers", "policy makers", "observers",
    "commentators", "the debate", "the sector", "organisations",
    "businesses", "the economy", "users", "consumers", "citizens",
    "the country", "we all", "all of us", "many", "some people",
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


# Crime guard. WE does not write about named people accused, charged, on
# trial or convicted of anything, and it does not touch live proceedings.
# Two separate risks sit here: defamation, where the accused person is the
# highest-risk subject in English law, and contempt of court, which is its
# own offence and does not care whether what you wrote was true.
#
# Cruder than the libel guard on purpose. No name has to be present. One of
# these words anywhere in the post sends it back. "Alleged" and "guilty"
# have perfectly innocent uses and will bounce good posts. That is the
# trade that was chosen.
CRIME = (
    "arrested",
    "charged",
    "convicted",
    "sentenced",
    "on trial",
    "accused",
    "alleged",
    "indicted",
    "jailed",
    "prosecution",
    "defendant",
    "acquitted",
    "guilty",
    "pleaded",
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
    # Struck-through corrections stay on the page but don't count against the
    # ceiling. If they did, every visible correction would push a post over
    # the limit and reward deleting history instead of striking it, which is
    # the exact behaviour the strike-through convention exists to prevent.
    text = re.sub(r"~~.*?~~", " ", text, flags=re.S)
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



def crime_words(body: str) -> list:
    """Sentences where the vocabulary of a criminal case sits next to a name.

    This guard began cruder: any of these words anywhere sent the post back,
    no name required, on the grounds that bouncing good posts was a fair
    price twice a week. Daily posts answering the news made that price four
    lost posts in a week, because writing about law, safety incidents or
    Dalrymple's East India Company without ever using "accused" or
    "prosecution" in their innocent senses is barely possible.

    The legal risks the guard exists for, defamation of an accused person
    and contempt of live proceedings, both need an identifiable somebody. So
    the hard stop now requires a proper noun in the same sentence, the same
    deliberately over-broad test the libel guard uses: any capitalised word
    that is not starting the sentence counts as a name. "The Hastings
    prosecution" still stops the post. "AI will make prosecution of fraud
    harder" no longer does. Nameless uses are flagged as rewrite pressure
    instead, in check_post, so they still get argued about, in public,
    without costing the day's post.
    """
    flagged = []
    for line in plain_text(body).split("\n"):
        for raw in re.split(r"(?<=[.!?])\s+", line):
            sentence = raw.strip()
            if not sentence:
                continue
            low = sentence.lower()
            hits = [
                w for w in CRIME
                if re.search(r"\b" + re.escape(w) + r"\b", low)
            ]
            if not hits:
                continue
            names = []
            for token in sentence.split()[1:]:
                token = token.strip(",;:.!?()[]\"'\u201c\u201d\u2018\u2019")
                if re.fullmatch(r"[A-Z][a-zA-Z'\u2019-]+", token):
                    names.append(token)
            if names:
                flagged.append((sentence, sorted(set(hits))))
    return flagged


def crime_words_nameless(body: str) -> list:
    """Crime vocabulary with nobody named: a style failure, not a hold."""
    flagged = []
    for line in plain_text(body).split("\n"):
        for raw in re.split(r"(?<=[.!?])\s+", line):
            sentence = raw.strip()
            if not sentence:
                continue
            low = sentence.lower()
            hits = [w for w in CRIME
                    if re.search(r"\b" + re.escape(w) + r"\b", low)]
            if not hits:
                continue
            names = [t for t in sentence.split()[1:]
                     if re.fullmatch(r"[A-Z][a-zA-Z'\u2019-]+",
                                     t.strip(",;:.!?()[]\"'\u201c\u201d\u2018\u2019"))]
            if not names:
                flagged.append(
                    f'Court vocabulary with nobody named: "{sentence[:130]}" '
                    f'[{", ".join(sorted(set(hits)))}]. Safe as written, but one '
                    "edit that adds a name makes it a legal problem, so find a "
                    "plainer word if one exists."
                )
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
    """Every n-word run carrying at least two words that mean something.

    Names are exempt. The National Audit Office turning up in two posts is
    a source appearing twice, not a writer repeating himself, and flagging
    it would push WE away from citing the same body about the same subject.
    """
    plain = plain_text(text)
    names = {w.lower() for w in proper_nouns(plain)}
    words = re.findall(r"[a-z']+", plain.lower())
    grams = set()
    for i in range(len(words) - n + 1):
        gram = words[i : i + n]
        meaty = [w for w in gram if w not in STOPWORDS]
        if len(meaty) >= 2 and sum(1 for w in meaty if w in names) < 2:
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


def recent_bench(n: int = 3) -> set:
    """Bench thinkers who spoke in any of the last n posts.

    By 28 August, imaginary Ostrom had appeared in seven of the nine posts
    that carry voices, including six in a row, while four of the seventeen
    on the bench had never spoken once. A jury drawn from the same corner
    every day stops being a jury. Nothing measured this, because the
    repetition check reads prose and the voices live in front matter.
    """
    import re as _re
    names = set()
    for f in sorted(POSTS.glob("*.md"))[-n:]:
        fm = f.read_text(encoding="utf-8").split("\n---\n", 1)[0]
        thinkers = _re.findall(r'thinker: "([^"]+)"', fm)
        kinds = _re.findall(r'kind: "([^"]+)"', fm)
        names.update(t for t, k in zip(thinkers, kinds) if k == "bench")
    return names


def check_voice_rotation(voices: list) -> list:
    """The bench rotates, or it is not a bench."""
    used = recent_bench()
    if not used:
        return []
    repeats = sorted({v.get("thinker", "") for v in voices
                      if v.get("kind") == "bench" and v.get("thinker") in used})
    if not repeats:
        return []
    return [
        "Bench thinkers already used in the last three posts: "
        + ", ".join(repeats) + ". Seventeen people sit on that bench and "
        "four of them have never spoken. Pick someone who has not been "
        "heard from lately. If the argument only works with the same "
        "juror every time, it is not the juror doing the work."
    ]


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


def check_bet_is_open(already) -> list:
    """A bet about something that already happened is not a bet.

    check_due_date only confirms the settle date is in the future, which a
    claim about last year passes cleanly. So the bet gets its own search.
    """
    if not isinstance(already, dict):
        return ["You have not checked whether the bet has already happened. "
                "Search for it before you make it. A future tense stuck on "
                "the front of a description is not a prediction."]
    searched = str(already.get("searched") or "").strip()
    answer = str(already.get("answer") or "").strip().lower()
    if len(searched.split()) < 3:
        return [f'The search for whether the bet already happened is not a '
                f'search: "{searched}" Write the query somebody would run to '
                "find out that you are too late."]
    if answer not in ("no", "yes"):
        return ['Answer yes or no: has it already happened? You wrote '
                f'"{already.get("answer")}".']
    if answer == "yes":
        return ["The bet has already happened, so it is not a bet. Say what "
                "already occurred, in the post, and then bet on what comes "
                "after it. Being late is only embarrassing if you publish it "
                "as a forecast."]
    return []


# What counts as a paper. The point of answering a published piece is that
# the argument is already in front of people, so a blog nobody reads is no
# use however good it is. Checked on the domain, because a publication name
# is typed by the writer and a domain is not.
MAINSTREAM = (
    "theguardian.com", "observer.co.uk", "thetimes.com", "thetimes.co.uk",
    "telegraph.co.uk", "ft.com", "independent.co.uk", "inews.co.uk",
    "dailymail.co.uk", "mirror.co.uk", "express.co.uk", "thesun.co.uk",
    "standard.co.uk", "metro.co.uk", "economist.com", "newstatesman.com",
    "spectator.co.uk", "prospectmagazine.co.uk", "unherd.com",
    "bbc.co.uk", "bbc.com", "news.sky.com", "channel4.com", "itv.com",
    "reuters.com", "bloomberg.com", "apnews.com",
    "scotsman.com", "heraldscotland.com", "yorkshirepost.co.uk",
    "walesonline.co.uk", "irishtimes.com", "belfasttelegraph.co.uk",
    "nytimes.com", "washingtonpost.com", "wsj.com", "theatlantic.com",
    "newyorker.com", "politico.eu", "politico.com", "lrb.co.uk", "nybooks.com",
)


def is_mainstream(url: str) -> bool:
    host = re.sub(r"^https?://", "", (url or "").strip().lower()).split("/")[0]
    host = host.split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return any(host == d or host.endswith("." + d) for d in MAINSTREAM)


def check_responds_to(responds_to) -> list:
    """Every post answers something somebody published this week.

    This was a standing note for a day and nothing came of it, because a note
    is guidance and there was no field to put the answer in. What gets checked
    happens. What gets merely instructed sometimes does not.
    """
    if not isinstance(responds_to, dict) or not str(responds_to.get("url") or "").strip():
        return ["No piece named. Every post answers one specific thing "
                "somebody published this week, by a named writer, in a paper "
                "or broadcaster the reader has heard of. Name it, link it, "
                "and say what in it you disagree with. If nothing out there "
                "is worth disagreeing with today, go to a different paper."]
    missing = [k for k in ("title", "author", "publication", "disagreement")
               if not str(responds_to.get(k) or "").strip()]
    if missing:
        return [f"The piece you are answering is missing: {', '.join(missing)}. "
                "A reader should be able to go and read the thing you are "
                "arguing with, and see what you are arguing about."]

    url = str(responds_to.get("url")).strip()
    if not is_mainstream(url):
        return [f"That is not a mainstream paper: {url} The whole reason for "
                "answering a published piece is that the argument is already "
                "in front of people, and a site nobody reads puts it in front "
                "of nobody. National papers, the broadsheets and the tabloids, "
                "the big magazines, the broadcasters, the wires. If the story "
                "is real, one of them has covered it. Go and answer that."]
    return []


def check_refutation(refutation, body: str = "") -> list:
    """One search aimed at killing your own argument, before you write it.

    Reporting a search was never enough. On 24 August a post searched around
    its subject, came back satisfied, and published a sentence saying the
    policy reached nobody but heat-pump owners. One search against that
    sentence would have found that every household buys electricity. So the
    search now has to name the sentence it is trying to kill, quote it from
    the post, and go at that.
    """
    if not isinstance(refutation, dict):
        return ["No refutation search. Before writing, search once for the "
                "strongest case that your argument is wrong, and report what "
                "came back."]
    searched = str(refutation.get("searched") or "").strip()
    did = str(refutation.get("what_it_did") or "").strip()
    claim = str(refutation.get("claim") or "").strip()
    failures = []

    if not claim:
        failures.append(
            f"{FACTUAL} You didn't name the sentence the argument stands on. "
            "Quote the one sentence from your post that, if false, takes the "
            "rest down with it. A post whose author cannot point at that "
            "sentence has not worked out what it is claiming."
        )
    elif body:
        # The quote has to be in the post. Compare on words, since a model
        # will paraphrase itself and punctuation drifts in a rewrite.
        want = content_words(claim)
        have = content_words(plain_text(body))
        if want and len(want & have) / len(want) < 0.6:
            failures.append(
                f'{FACTUAL} The sentence you say the argument rests on is not '
                f'in the post: "{claim[:120]}" Quote it from the body, word '
                "for word. If it is not in there, the post is not making the "
                "claim you think it is making."
            )
        elif searched:
            # And the search has to be aimed at it.
            aimed = content_words(searched) & want
            if not aimed:
                failures.append(
                    f'{FACTUAL} The refutation search does not go at the '
                    f'load-bearing sentence. You said the argument stands on '
                    f'"{claim[:90]}" and then searched "{searched[:90]}". '
                    "Those share nothing. Search against the sentence itself, "
                    "the way somebody trying to prove you wrong would."
                )

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


def content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z']{4,}", (text or "").lower())
            if w not in STOPWORDS}


def proper_nouns(body: str) -> set:
    """Capitalised words that aren't starting a sentence. A rough count of
    how many specific things the post actually names."""
    found = set()
    for s in sentences(body):
        for token in s.split()[1:]:
            token = token.strip(",;:.!?()[]\"'\u201c\u201d\u2018\u2019")
            if re.fullmatch(r"[A-Z][a-zA-Z'\u2019-]+", token):
                found.add(token)
    return found


def check_specificity(body: str) -> list:
    """The general is predictable by construction. The particular is not."""
    if visible_words(body) < 200:
        return []
    named = proper_nouns(body)
    if len(named) >= 4:
        return []
    return [
        f"The post names {len(named)} specific things. A piece built out of "
        "categories cannot surprise anybody, because a category is the "
        "average of its cases and the reader can already guess it. Name the "
        "body, the place, the document, the date, the object. Not a local "
        "official. A man with a laminated sign."
    ]


def check_stakes(stakes) -> list:
    """Who cares. If you cannot answer it, do not write the post."""
    if not isinstance(stakes, dict):
        return ["No stakes. Before anything else: who does this happen to, "
                "what does it cost them, and why this week. If you cannot "
                "answer all three, the post has no reason to exist and no "
                "amount of good writing will give it one."]
    who = str(stakes.get("who") or "").strip()
    cost = str(stakes.get("cost") or "").strip()
    now = str(stakes.get("why_now") or "").strip()
    failures = []

    if not who:
        failures.append("Nobody is named as affected.")
    else:
        low = who.lower()
        vague = [n for n in NOBODIES if re.search(rf"\b{re.escape(n)}\b", low)]
        if vague and len(who.split()) < 12:
            failures.append(
                f'"{who}" is not a person this happens to. '
                + ", ".join(f'"{v}"' for v in vague)
                + " names nobody. Say who: the graduate applying for a job "
                "she will not get, the developer holding a connection he "
                "cannot use. A named kind of person in a describable "
                "situation."
            )
    if not cost:
        failures.append(
            "You have not said what it costs them. Money, time, a job, a "
            "choice they used to have. If the answer is that it costs them "
            "nothing, nobody cares, and they are right not to."
        )
    if not now:
        failures.append(
            "You have not said why this week. Something changed, or somebody "
            "decided, or a number crossed a line. Without that this is an "
            "essay about a condition, and conditions have no readers."
        )
    return failures


def check_recognition(recognition: str, body: str) -> list:
    """The thing everyone has half-noticed and nobody has written down."""
    said = (recognition or "").strip()
    if not said:
        return ["No recognition. Every post says one thing the reader has "
                "already half-noticed and never seen written down. Not a fact "
                "they lacked. A description of something they had clocked and "
                "never put words to. That is the line they will quote."]
    want = content_words(said)
    if len(want) >= 4 and len(want & content_words(body)) < len(want) * 0.4:
        return ['You named the recognition and then kept it out of the post: '
                f'"{said}" Say it, in the writing, in the plainest words you '
                "have."]
    return []


def check_prediction_placement(prediction: str, body: str) -> list:
    """The bet goes early or in the middle. Never as the sign-off.

    In three drafts running it landed in the same slot, second from last,
    which turns a claim about the future into a closing formality.
    """
    want = content_words(prediction)
    if len(want) < 4:
        return []
    paras = [p for p in body.split("\n\n") if p.strip()]
    if len(paras) < 4:
        return []

    present = want & content_words(body)
    if len(present) < len(want) * 0.4:
        return [
            "The prediction never actually appears in the post. It is not a "
            "field to fill in. Say it to the reader, in the writing, where "
            "they will see it."
        ]

    tail = "\n\n".join(paras[-max(1, len(paras) // 3):])
    in_tail = want & content_words(tail)
    if len(in_tail) >= len(present) * 0.6:
        return [
            "The bet is sitting in the last third again. Three posts running "
            "it landed in the same slot and it has become a beat: argument, "
            "argument, bet, sign-off. Move it up. A post that opens on its "
            "own prediction and then spends four hundred words earning it is "
            "a different piece of writing. End on something that lands, not "
            "on something that has not happened yet."
        ]
    return []


def load_predictions() -> list:
    if not PREDICTIONS.exists():
        return []
    try:
        return json.loads(PREDICTIONS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_predictions(rows: list) -> None:
    PREDICTIONS.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")


def due_predictions(today: str) -> list:
    """Bets whose date has passed and which nobody has judged yet."""
    return [p for p in load_predictions()
            if p.get("status") == "open" and str(p.get("due", "")) <= today]


def check_due_verdicts(verdicts, today: str) -> list:
    """Every bet that has come due gets judged, in the open, this run."""
    outstanding = due_predictions(today)
    if not outstanding:
        return []
    given = {}
    if isinstance(verdicts, list):
        for v in verdicts:
            if isinstance(v, dict) and v.get("id"):
                given[str(v["id"])] = v

    failures = []
    for row in outstanding:
        rid = str(row.get("id"))
        v = given.get(rid)
        if not v:
            failures.append(
                f'A bet came due and you have not judged it. {row.get("due")}: '
                f'"{row.get("claim")}" Say right, wrong or too early, and say '
                "it in the post before anything else. This is the only thing "
                "on the site that can cost you anything."
            )
            continue
        if str(v.get("verdict")) not in ("right", "wrong", "too early"):
            failures.append(
                f'Verdict on "{row.get("claim")}" must be right, wrong or too '
                f'early. You wrote "{v.get("verdict")}".'
            )
        elif not str(v.get("note") or "").strip():
            failures.append(
                f'You judged "{row.get("claim")}" and said nothing about it. '
                "One line: what actually happened."
            )
    return failures


def apply_verdicts(verdicts, today: str) -> None:
    rows = load_predictions()
    given = {str(v["id"]): v for v in (verdicts or [])
             if isinstance(v, dict) and v.get("id")}
    for row in rows:
        v = given.get(str(row.get("id")))
        if v and row.get("status") == "open":
            row["status"] = str(v.get("verdict"))
            row["note"] = str(v.get("note") or "").strip()
            row["resolved"] = today
    save_predictions(rows)


def check_due_date(due: str, today: str) -> list:
    due = (due or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", due):
        return ['The prediction needs a date it can be judged on, as '
                f'YYYY-MM-DD. You wrote "{due}".']
    if due <= today:
        return [f"The prediction comes due on {due}, which is not in the "
                "future. A bet you can already settle is not a bet."]
    return []


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


def record_about(update, date: str, title: str) -> None:
    """Add to the top of the About page. Never overwrite what's underneath.
    Changing your mind in public only counts if what you changed from is
    still there to be read."""
    if not isinstance(update, dict) or not update.get("changed"):
        return
    text = str(update.get("what") or "").strip()
    if not text:
        return
    existing = ABOUT.read_text(encoding="utf-8") if ABOUT.exists() else ""
    if ABOUT_MARK not in existing:
        return
    head, _, rest = existing.partition(ABOUT_MARK)
    why = str(update.get("why") or "").strip()
    entry = f"\n\n## Revised {date}, after \"{title}\"\n\n"
    if why:
        entry += f"*What moved it: {why}*\n\n"
    entry += text.strip() + "\n\n---\n"
    ABOUT.write_text(head + ABOUT_MARK + entry + rest, encoding="utf-8")


def record_prediction(prediction: str, due: str, title: str, date: str, url: str) -> None:
    rows = load_predictions()
    rows.insert(0, {
        "id": f"{date}-{len(rows) + 1}",
        "made": date,
        "due": due,
        "claim": prediction.strip(),
        "post": title,
        "url": url,
        "status": "open",
        "note": "",
        "resolved": "",
    })
    save_predictions(rows)


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


# The model talking to itself. It happens when a rewrite goes wrong: the
# working leaks out of the draft and into the post, and gets published as
# though it were prose. On 23 August a post went out containing "Wait. No em
# dashes. Again." followed by a corrected paragraph. Twenty-one checks and not
# one saw it, because every other check reads a post as writing rather than as
# the transcript of somebody producing writing.
SELF_TALK = (
    r"(?:^|[.!?]\s+|\n)\s*wait\s*[.!]",
    r"\bno em[- ]dash",
    r"\blet me (?:rewrite|redo|try|fix|start|cut|shorten|have another)",
    r"\bi (?:need|have|ought) to (?:rewrite|redo|fix|cut|shorten|start)",
    r"\bscratch that\b",
    r"\bstarting over\b",
    r"\btry (?:that|this|it) again\b",
    r"\bthe brief (?:says|bans|wants|requires|forbids|calls)\b",
    r"\brewrit(?:e|ing) (?:that|this|it)\b",
    r"\b(?:as|per) (?:instructed|the brief)\b",
    r"\bthat (?:sentence|paragraph|line) (?:is|was) too\b",
    r"\bcorrected version\b",
    r"\battempt \d",
)


# Authority with nobody behind it. "Some researchers think" is the sound a
# model makes when it wants the weight of a citation without having one, and
# it reads as generated to anyone who has seen it before. Either name them or
# drop the claim.
UNNAMED_AUTHORITY = (
    "some researchers", "researchers think", "researchers believe",
    "researchers say", "studies show", "studies suggest", "studies have shown",
    "experts say", "experts believe", "experts agree", "many experts",
    "it is thought", "it is believed", "it is widely", "it has been argued",
    "some argue", "some say", "critics say", "observers say",
    "data suggests", "evidence suggests", "research suggests",
    "commentators", "analysts say",
)


def check_unnamed_authority(body: str) -> list:
    """Borrowed weight with nobody's name on it."""
    low = plain_text(body).lower()
    hits = sorted({p for p in UNNAMED_AUTHORITY if p in low})
    if not hits:
        return []
    return [
        "Authority with nobody behind it: " + ", ".join(f'"{h}"' for h in hits)
        + ". Name who, and link them, or cut the claim and say the thing in "
        "your own voice with no borrowed weight. A reader who has met a "
        "chatbot recognises this construction, and it costs you every other "
        "sourced claim in the post."
    ]


# Every correction made to this site on 23 August was a number or a citation.
# Not one was an argument that fell down. The checks below this line measure
# how prose reads; none of them asked where a figure came from, and a model is
# most confident exactly where it is inventing a plausible statistic. So: a
# quantity, a comparison or a named study must have a link in the same
# sentence, or it does not go out.

# Quantities that carry weight. Bare years are left alone, because a
# prediction is full of them and needs no citation to be a prediction.
QUANTITY = re.compile(
    r"(?<![\w.])(?:"
    r"[£$€]\s?\d[\d,.]*"                     # money
    r"|\d[\d,.]*\s?(?:%|per cent|percent)"    # proportions
    r"|\d{1,3}(?:,\d{3})+"                     # 674,000
    r"|\d+\.\d+"                              # decimals
    r")",
    re.I,
)

# A comparison with no number attached is the same problem wearing a word.
COMPARISON = re.compile(
    r"\b(?:roughly |about |nearly |around |some )?"
    r"(?:half|double|twice|treble|triple|[a-z]+ times)\s+"
    r"(?:that of|as (?:many|much|likely|high|low)|the (?:rate|number|level))"
    r"|\b(?:more|less) likely (?:to|than)\b",
    re.I,
)

# Somebody else's authority, named but unlinked.
NAMED_STUDY = re.compile(
    r"\b(?:a|the|one)\s+\d{4}\s+(?:study|paper|report|survey|review|trial)"
    r"|\b(?:study|paper|research|analysis|survey)\s+(?:in|by|from|published in)\s+[A-Z]"
    r"|\baccording to (?:a|the|one)\s",
    re.I,
)

HAS_LINK = re.compile(r"\]\([^)]+\)")


def check_sourcing(body: str) -> list:
    """A number, a comparison or a named study with no link beside it."""
    failures = []
    # Struck-out wording is a quotation of what this post used to say. It is
    # already marked as wrong on the page and is not being claimed, so asking
    # it for a source would be asking a correction to justify the error.
    body = re.sub(r"~~.*?~~", " ", body, flags=re.S)
    for para in body.split("\n"):
        for raw in re.split(r"(?<=[.!?])\s+", para):
            sentence = raw.strip()
            if not sentence or HAS_LINK.search(sentence):
                continue
            bare = re.sub(r"[#>*_`~]", " ", sentence)
            # A figure attributed to a named body in the same sentence is
            # traceable even unlinked: "the SRA's 2025 data shows 66%" tells a
            # reader where to look. A figure floating free does not. The test
            # is a capitalised word that is not just the start of a sentence.
            attributed = bool(re.search(r"(?<!^)(?<![.!?] )\b[A-Z][A-Za-z&']+", bare[1:]))
            linked_para = bool(HAS_LINK.search(para))
            found = []
            if QUANTITY.search(bare) and not attributed and not linked_para:
                found.append("a figure")
            if COMPARISON.search(bare) and not linked_para:
                found.append("a comparison")
            # A named study always needs the link. Naming a journal is exactly
            # how an invented citation gets its authority, and the whole point
            # of a citation is that somebody can go and read the thing.
            if NAMED_STUDY.search(bare):
                found.append("a cited authority")
            if found:
                failures.append(
                    f'{FACTUAL} {" and ".join(found).capitalize()} with no link '
                    f'beside it: "{sentence[:150]}" Put the source in that '
                    "sentence or take the claim out. A figure a reader cannot "
                    "follow is a figure you are asking them to take on trust, "
                    "and this site has spent its credibility on that once "
                    "already. A rate needs its denominator too: per what."
                )
    return failures


def check_self_talk(body: str) -> list:
    """Working that leaked into the post. Nothing about the brief, the checks
    or the rewriting belongs in front of a reader."""
    low = plain_text(body).lower()
    hits = sorted({" ".join(m.group(0).split()).strip(".!? ")
                   for p in SELF_TALK for m in re.finditer(p, low)})
    hits = [h for h in hits if h]
    if not hits:
        return []
    return [
        "Your working is in the post: " + ", ".join(f'"{h}"' for h in hits)
        + ". You were talking to yourself about the rewrite and it went into "
        "the writing. A reader has no idea what you are referring to and no "
        "reason to care. Cut every trace of it. Nothing about the brief, the "
        "checks, the rewrites or your own drafting belongs in a post."
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
    failures += check_self_talk(body)
    failures += crime_words_nameless(body)
    failures += check_unnamed_authority(body)
    failures += check_sourcing(body)

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

    crime = crime_words(body)
    if crime:
        quoted = "\n".join(
            f'      "{s}"\n        [{", ".join(w)}]' for s, w in crime
        )
        failures.append(
            "Crime vocabulary. The brief says never write about a named "
            "person accused, charged, on trial or convicted of anything, and "
            "never about live proceedings:\n" + quoted + "\n"
            "    Two risks, not one: an accused person is the most dangerous "
            "subject in English defamation law, and commenting on an active "
            "case is contempt of court whether or not it's true. Write about "
            "the rule, the institution or the law itself, with nobody's case "
            "in it. If the post only works with the case in it, write a "
            "different post. This check over-triggers and that is deliberate, "
            "so if it's an innocent use of the word, use another word."
        )

    return failures


# The three questions from the brief's defamation rules, answered by the
# writer about its own post. Anything that is not a flat "no" stops the
# post. Absent or unreadable counts as a yes: a gate that fails open is
# not a gate.
GATE_QUESTIONS = {
    "damaging_claim": (
        "Could an identifiable living person or organisation reasonably say "
        "this post makes a factual claim that seriously harms their "
        "reputation?"
    ),
    "repeats_allegation": (
        "Does the post repeat, restate or rest on an allegation anyone has "
        "made about an identifiable person or organisation?"
    ),
    "private_material": (
        "Does the post rely on leaked, private or confidential material?"
    ),
}


def check_reputation_gate(gate) -> list:
    """The writer's own answers to the three gate questions."""
    if not isinstance(gate, dict):
        return [
            "No reputation_gate in the reply. The brief requires the three "
            "defamation questions answered before anything publishes, and a "
            "missing answer is treated as a yes. Answer all three."
        ]
    failures = []
    for key, question in GATE_QUESTIONS.items():
        answer = str(gate.get(key, "")).strip().lower()
        if answer == "no":
            continue
        if answer not in ("yes", "maybe", "uncertain", ""):
            answer = f'unreadable ("{answer}")'
        failures.append(
            f"Reputation gate, {key}: {answer or 'unanswered'}. {question} "
            "The brief says yes, maybe or uncertain all stop the post. "
            "Rewrite it so the honest answer is no. Criticise the rule, the "
            "law or the institution, and take the identifiable person or "
            "company out of it. If the post only works with them in it, it "
            "is the wrong post."
        )
    return failures


# Prefix on any failure that is about what is true rather than how it reads.
# Style failures publish anyway after two rewrites, loudly, because an
# unedited miss is honest and the reader can see it. A factual failure is not
# a miss. Publishing forty words long is a blemish; publishing something a
# source does not carry is a different kind of thing, and it is worse now that
# every post names a living journalist and says they are wrong.
FACTUAL = "[FACT]"


def factual_failures(failures: list, unverified: list) -> list:
    """The failures that must not publish, however many rewrites have gone."""
    reasons = [f for f in failures if f.startswith(FACTUAL)]
    for s in unverified:
        reasons.append(
            f"Cited a source no search returned: {s['title']} ({s['url']}). "
            "Either the link is wrong or the claim came from somewhere other "
            "than the evidence. A reader following it finds out which."
        )
    return reasons


def legal_risk(body: str, gate_failures: list) -> list:
    """What must never publish without a person reading it first.

    Separate from the ordinary brief failures on purpose. Those publish
    anyway after two rewrites, loudly, because an unedited miss is honest.
    A defamation risk is not a miss. It is the one thing a rewrite loop is
    not allowed to wave through.
    """
    reasons = list(gate_failures)
    for sentence, words, names in accusing_sentences(body):
        reasons.append(
            f'Accusing word next to a name: "{sentence}" '
            f'[{", ".join(words)} + {", ".join(names)}]'
        )
    for sentence, words in crime_words(body):
        reasons.append(f'Crime vocabulary: "{sentence}" [{", ".join(words)}]')
    return reasons


def hold(post: dict, reasons: list, date: str, slug: str) -> None:
    """Stop the post and put it where only a human can pick it up."""
    HELD.mkdir(parents=True, exist_ok=True)
    path = HELD / f"{date}-{slug}.md"
    path.write_text(
        f"# HELD FOR HUMAN REVIEW: {post['title']}\n\n"
        + "\n".join(f"- {r}" for r in reasons)
        + "\n\n---\n\n"
        + post["body"].strip()
        + "\n",
        encoding="utf-8",
    )
    print("!" * 60)
    print("HELD. NOT PUBLISHED. NEEDS A HUMAN.")
    print(f"  title: {post['title']}")
    for r in reasons:
        print(f"  - {r}")
    print(f"  draft: {path}")
    print("!" * 60)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        lines = [
            f"### WE held `{date}-{slug}` for human review",
            "",
            "Nothing was published, committed or announced. The draft is not "
            "in this repository: a public repo is publication, so a post "
            "stopped for a reputation risk does not go into one.",
            "",
        ]
        lines += [f"- {r}" for r in reasons]
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def set_output(held: bool) -> None:
    """Tell the workflow whether anything was published this run."""
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"held={'true' if held else 'false'}\n")


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
  "obvious_ending": true or false,
  "obvious_ending_because": "the last line, and the reason anybody would have written it. empty if it swerves",
  "over_explained": ["any place the post makes a point and then explains it, quote the redundant sentence"],
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

First, before anything about the writing. Who cares? Name the person this happens to and what it costs them. If the honest answer is that it matters to people who follow this subject professionally, the post has no reason to exist and you should say so, however well made it is. Good writing about nothing is still nothing.

Is it dull? Not imperfect, dull. Would anyone who is not paid to be here reach the end. Reserve dull for a piece with no reason to exist, and if that is the honest answer, say it.

Then look specifically for the things that make prose lifeless even when the argument is good. Is there a single real image anywhere, or is it abstract nouns end to end. Is there one line that is actually funny. Does the writer appear to want anything, or is the whole thing delivered at the same polite temperature from start to finish. Say which of these is missing, by name.

Read the last line. Was that the ending anybody would have written? A reader is a few words ahead by the final paragraph, and if the post lands exactly where they were already standing, nothing happens. Say what the obvious ending was and whether this is it.

Then find every place the post makes a point well and then explains it. The sentence after the good line, restating it in case the reader missed it. Quote each one. Those sentences take the reader's own thought away from them and give it to nobody, and cutting them is the cheapest improvement available to any piece of writing.

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

    if verdict.get("obvious_ending"):
        failures.append(
            "The critic says the ending is the one anybody would have "
            f"written: {verdict.get('obvious_ending_because') or '(no reason given)'} "
            "Write two more and use the third."
        )

    for item in verdict.get("over_explained") or []:
        failures.append(
            f"Explaining your own point: {item} Cut it. The reader had it, "
            "and you just took it off them."
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
            f"{FACTUAL} The critic doesn't accept a source: {item} Find "
            "something that carries the claim, or cut the claim."
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


def current_about() -> str:
    if not ABOUT.exists():
        return "(no about page)"
    text = ABOUT.read_text(encoding="utf-8")
    _, _, body = text.partition(ABOUT_MARK)
    return (body or text).strip()


def past_predictions() -> str:
    rows = load_predictions()
    if not rows:
        return "(nothing predicted yet)"
    out = []
    for r in rows[:20]:
        status = r["status"] if r["status"] != "open" else f"open, due {r['due']}"
        line = f"- [{r['id']}] {r['claim']} ({status})"
        if r.get("note"):
            line += f"\n      what happened: {r['note']}"
        out.append(line)
    return "\n".join(out)


def due_now(today: str) -> str:
    rows = due_predictions(today)
    if not rows:
        return "(nothing has come due this run)"
    return "\n".join(
        f"- [{r['id']}] due {r['due']}: {r['claim']}" for r in rows
    )


def critic_notes() -> str:
    if not CRITIC.exists():
        return "(no critic notes yet)"
    return CRITIC.read_text(encoding="utf-8").strip() or "(no critic notes yet)"


def operator_notes() -> str:
    """Everything below the file's own header. The prompt supplies the framing,
    so the file's title would only say it twice."""
    if not NOTES.exists():
        return "(nothing said yet)"
    text = NOTES.read_text(encoding="utf-8")
    _, sep, body = text.partition("\n---\n")
    return (body if sep else text).strip() or "(nothing said yet)"


TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


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

## The bench, rotated

Barred today, because they spoke in the last three posts:
{", ".join(sorted(recent_bench())) or "(nobody barred)"}

Seventeen sit on the bench. Draw from the ones who have not spoken lately.
The same juror every day stops being a jury.

---

## What the person running WE has said

Standing notes from whoever points this thing. Not a brief and not a style
guide: judgements made after reading posts that had already gone out. They
outrank your own instincts where the two disagree, because they come from
somebody who read the work cold and had nothing to defend.

You cannot edit this file.

{operator_notes()}

---

## Your thesis as it currently stands

{current_thesis()}

---

## How the site describes itself

This is the About page. It was written on 21 August, before the bench, the
critic, the bets and the scoreboard existed, so it describes a smaller
project than the one now running. Anyone arriving from anywhere else reads
it before they read a post.

If it no longer describes what WE does, rewrite it. Same rule as the thesis:
the new version goes on top, the old one stays underneath, and you say what
moved it. Describe the thing as it actually works. Do not sell it.

{current_about()}

---

## Bets that have come due

Judge every one of these in this post, before anything else. Right, wrong,
or too early, and one line on what actually happened. Nobody else on the
internet does this and it is the only thing here that can cost you
anything.

{due_now(TODAY)}

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
- Answers who cares. A person it happens to, what it costs them, and
  why this week. If you cannot, do not write it.
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
- Names at least four specific things. A body, a place, a document, a
  date, an object. Not categories.
- Says one thing the reader has already half-noticed and never seen
  written down.
- Ends somewhere they were not already standing, and never explains a
  point it has just made.
- Uses one polemical move on purpose, and not the one you used last time.
- Makes the other case without announcing that it is being fair.
- Says the strong version. No hedges bought with the reader's attention,
  and it doesn't stop one step short of where its own argument goes.
- Judges every bet that has come due, at the top, before anything else.
- Searched to check the new bet has not already happened. A future tense
  on the front of a description is not a prediction.
- Says what happens next, with a date, in a form that could be wrong.
  Not hedged into safety, and not parked in the last third as a
  sign-off. Put it early and spend the post earning it.
- Uses history as evidence, never as the subject.
- Came from a vantage point somebody else isn't already standing at.
- If it talks about a job, somebody who does that job answers back.
- Do not write the human voice. A reader who did not write the post adds
  it afterwards, and you will be asked to fix whatever they object to
  before it is published.
- Says whether the thesis moved, and if not, what would move it.
- Says whether the About page still describes this project honestly, and
  rewrites it if it does not. The version it replaces stays underneath.
- Doesn't open on a statistic. No price, percentage or count in the
  first sentence.
- Doesn't reuse an opening move or a turn of phrase from an earlier
  post. Read the last five before you start.
- No accusing word anywhere near a named person or company. Attack the
  rule, never whoever benefits from it. This one is a legal matter, not a
  style note.
- Answers the three defamation questions honestly in reputation_gate.
  Anything other than no on all three stops the post dead. It does not
  publish with a warning attached, the way a missed brief rule does. It
  goes to a person and waits. Guessing no to get past the gate is the
  worst thing you could do here, because the gate is the only thing
  standing between this site and somebody's solicitor.
- No named person accused, charged, arrested, on trial or convicted of
  anything, and nothing about a live case, inquiry or investigation into
  a named individual. Not even one everybody is already discussing.
- Never states an allegation as fact. If the source says someone alleged
  it, the post says someone alleged it, and says who.
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
  "prediction_due": "YYYY-MM-DD, the day this can be settled",
  "bet_already_happened": {{"searched": "the query you ran to find out whether your prediction has already come true",
                           "answer": "yes or no"}},
  "verdicts": [{{"id": "the id of a bet that has come due", "verdict": "right, wrong or too early", "note": "one line on what actually happened"}}],
  "derived_number": {{"figure": "one number that appears in none of your sources, worked out from ones that do",
                     "working": "the arithmetic, shown, from which published figures",
                     "sources": ["the urls the input numbers came from"]}},
  "stakes": {{"who": "the kind of person this happens to, in a describable situation. not society, not the industry",
             "cost": "what it costs them. money, time, a job, a choice they used to have",
             "why_now": "what changed, who decided, or which number crossed a line, this week rather than any other"}},
  "responds_to": {{"title": "the headline of the piece this post answers",
                  "author": "who wrote it",
                  "publication": "the paper or site it ran in",
                  "date": "YYYY-MM-DD, when it was published",
                  "url": "the link to it",
                  "disagreement": "the specific thing in that piece you are disagreeing with, in one sentence. Not the subject. The claim."}},
  "recognition": "the thing readers have already half-noticed about this and never seen written down, in one plain sentence",
  "refutation": {{"claim": "the one sentence in your post that, if it turned out to be false, would take the whole argument down with it. Quote it from the body, word for word. Not the subject, not the thesis in general: the load-bearing sentence.",
                 "searched": "the query you ran to find the strongest case that THAT SENTENCE is wrong. Aim at the sentence, not the topic.",
                 "found": "the best counter-evidence it returned, or empty if it came back with nothing",
                 "what_it_did": "how that changed the post",
                 "won": "true if the counter-evidence beat your original idea and this post is now about that instead"}},
  "technique": "which polemical move you used this time, one of: reversal, refrain, their own words, register collision, straight face, concrete swap, the list that argues, the sentence that turns",
  "jury_notes": "what three of the bench each noticed that the others could not see. a short paragraph. this is working, not prose",
  "thesis_update": {{"changed": true or false,
                    "what": "what changed in the thesis and what moved it, or empty",
                    "would_change_it": "if nothing changed, what evidence would"}},
  "reputation_gate": {{"identifiable": "every living person or organisation a reader could work out from this post, named or not. empty if none",
                      "damaging_claim": "yes, maybe or no. could any of them reasonably say this post makes a factual claim that seriously harms their reputation",
                      "repeats_allegation": "yes, maybe or no. does the post repeat, restate or rest on an allegation anyone has made about an identifiable person or organisation",
                      "private_material": "yes, maybe or no. does the post rely on leaked, private or confidential material",
                      "why": "one line on the riskiest sentence in the post and why it is or is not safe"}},
  "sources": [{{"title": "what it is", "url": "https://..."}}],
  "voices": [{{"thinker": "Karl Marx", "kind": "bench", "lived": "1818 to 1883",
              "argument": "how the argument runs, in your words, no quote marks, never first person",
              "quote": "only real searched words, or empty",
              "quote_url": "the link a search returned, or empty"}},
             {{"kind": "practitioner", "thinker": "lawyer",
              "argument": "a few sentences from somebody who does the job, on what the post gets wrong about it"}},
             ],
  (a human voice is added afterwards by a reader who did not write the post: do not write one yourself)
  "about_update": {{"changed": true or false,
                   "what": "the complete new description of the site in markdown, headings and all, or empty",
                   "why": "what changed about the project that made the old description wrong"}},
  "agenda_update": "the complete new contents of agenda.md, in markdown"
}}"""


# --------------------------------------------------------------------------
# writing it out
# --------------------------------------------------------------------------


def yaml_str(value: str) -> str:
    """A YAML double-quoted scalar. JSON's escaping is valid YAML, but keep
    the accents as themselves: these files are meant to be read."""
    return json.dumps(value, ensure_ascii=False)


def front_matter(title: str, now: datetime, sources: list, voices: list,
                 responds_to: dict = None) -> str:
    lines = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        f"date: {now.isoformat()}",
        "layout: post.njk",
    ]
    if responds_to and str(responds_to.get("url") or "").strip():
        lines.append("responds_to:")
        for key in ("title", "author", "publication", "date", "url"):
            value = str(responds_to.get(key) or "").strip()
            if value:
                lines.append(f"  {key}: {yaml_str(value)}")
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


# Set by --draft. A draft run writes the post and nothing else: no agenda
# rewrite, no thesis revision, no bet recorded, no About revision. Iterating
# on a post should not leave five thesis versions and five bets behind.
DRAFT = "--draft" in sys.argv


def load_env() -> None:
    """Read .env if the key is not already in the environment. Gitignored, so
    it stays on this machine. Nothing here is printed, logged or committed."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def main() -> int:
    # One post per day. The schedule now fires at three separate times,
    # because GitHub's cron missed two mornings out of four and ran late on
    # the others. Whichever firing arrives first writes the post; the rest
    # find it already on disk and stand down. A held=true output is how the
    # announce job is told there is nothing to announce.
    if list(POSTS.glob(f"{TODAY}-*.md")):
        print(f"A post dated {TODAY} already exists. Standing down.")
        set_output(held=True)
        return 0

    load_env()
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
            max_tokens=MAX_TOKENS,
            tools=TOOLS,
            messages=messages,
        )
        searches += sum(
            1 for b in resp.content if getattr(b, "type", None) == "server_tool_use"
        )
        merge_sources(searched, harvest_sources(resp))
        # The model sometimes narrates its way through the searches and never
        # emits the JSON, or runs out of room mid-object. That is a formatting
        # accident, not a judgement, and it should cost a retry rather than the
        # whole run. Retries here are cheap; a crashed scheduled run is not.
        try:
            post = extract_json(text_blocks(resp))
        except ValueError as exc:
            print(f"Attempt {attempt + 1} returned no usable JSON: {exc.args[0][:120]}")
            if attempt == MAX_RETRIES:
                raise
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                "That reply contained no JSON object. Do not narrate, do not "
                "explain, do not search again. Reply with the JSON object "
                "described in the brief and nothing else, complete and valid, "
                "starting with { and ending with }."})
            continue
        voices = clean_voices(post.get("voices"))
        gate_failures = check_reputation_gate(post.get("reputation_gate"))
        failures = check_post(post["body"], published)
        failures += gate_failures
        failures += check_voices(voices, {s["url"] for s in searched})
        failures += check_voice_rotation(voices)
        failures += check_practitioner(post["body"], voices)
        failures += check_prediction(post.get("prediction"))
        failures += check_prediction_placement(post.get("prediction"), post["body"])
        failures += check_due_date(post.get("prediction_due"), TODAY)
        failures += check_due_verdicts(post.get("verdicts"), TODAY)
        failures += check_bet_is_open(post.get("bet_already_happened"))
        failures += check_derived_number(
            post.get("derived_number"), post["body"], {s["url"] for s in searched}
        )
        failures += check_refutation(post.get("refutation"), post["body"])
        failures += check_responds_to(post.get("responds_to"))
        failures += check_specificity(post["body"])
        failures += check_recognition(post.get("recognition"), post["body"])
        failures += check_stakes(post.get("stakes"))
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
    # A draft goes to one fixed file that the next draft overwrites, so
    # iterating on a post cannot litter the posts directory with attempts.
    path = (ROOT / "agent" / "draft.md") if DRAFT else POSTS / f"{date}-{slug}.md"

    # The gate. Everything above this line can be rewritten and published
    # with its failures showing. Nothing below it happens if a reputation
    # risk survived the rewrites: no post, no agenda update, no prediction
    # recorded, no announcement. A person reads it or it does not exist.
    risks = legal_risk(post["body"], gate_failures)
    risks += factual_failures(failures, unverified)
    if risks:
        hold(post, risks, date, slug)
        set_output(held=True)
        return 0

    # Front matter, then the body exactly as the model wrote it. No edits.
    path.write_text(
        front_matter(post["title"], now, sources, voices,
                     post.get("responds_to"))
        + "\n"
        + post["body"].strip()
        + "\n",
        encoding="utf-8",
    )

    if not DRAFT:
        AGENDA.write_text(post["agenda_update"].strip() + "\n", encoding="utf-8")

    # Never in a draft run. latest.json is what the announce step reads, and
    # pointing it at a post that was never published would tweet a 404.
    if not DRAFT:
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
    else:
        short = post["short_version"].strip()
        print(f"\n--- the post it would tweet, {len(short)} of 280 ---\n{short}\n")

    if verdict:
        record_critique(verdict, post["title"], date)
    if not DRAFT:
        apply_verdicts(post.get("verdicts"), date)
        record_prediction(post.get("prediction", ""), post.get("prediction_due", ""),
                          post["title"], date, f"{SITE}/posts/{date}-{slug}/")
        record_thesis(post.get("thesis_update"), date, post["title"])
        record_about(post.get("about_update"), date, post["title"])
    else:
        print(f"\nDRAFT RUN. Post written to {path}.")
        print("Agenda, thesis, About, bets and verdicts left untouched.")

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
    set_output(held=False)
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
