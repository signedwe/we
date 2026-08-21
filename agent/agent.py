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
        thinker = re.sub(r"^imaginary\s+", "", thinker, flags=re.I)
        argument = str(v.get("argument") or "").strip()
        if not thinker or not argument:
            continue
        out.append(
            {
                "thinker": thinker,
                "lived": str(v.get("lived") or "").strip(),
                "argument": argument,
                "quote": str(v.get("quote") or "").strip(),
                "quote_url": str(v.get("quote_url") or "").strip(),
            }
        )
    return out


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

        if re.search(r"\bI\b|\bmy\b|\bmine\b", v["argument"]):
            failures.append(
                f"The {who} voice is written in the first person. You are not "
                "speaking as them and the post must never look like you are. "
                "Write it as a description of the argument."
            )

        surname = who.split()[-1]
        m = re.search(rf"\b{re.escape(surname)}\b", v["argument"], re.I)
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
  "same_post": true or false,
  "same_post_because": "which earlier post, and what shape they share. empty if not",
  "bad_sources": ["for each weak citation: the claim, the source, why it will not carry it"],
  "hateful": ["anything racist, misogynistic or hateful, in the post or in a voice. usually empty"],
  "idle_voices": ["any voice that agrees with the post and is doing no work"],
  "unanswered": "the strongest objection the post does not deal with, or empty",
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

Is it the same post as one of the earlier ones? Same shape, not same words. Opens the same way, concedes in the same place, lands the same closing move, points the core question at the same kind of target.

Are the sources any good? Take each claim that carries a citation and ask what the source actually is. A press release is not evidence for a global statistic. A company blog is not evidence for a market forecast that company sells into. Search if you need to check what a source is. Name the claim, the source, and why it will not carry the weight.

Is anything in it racist, misogynistic or hateful, in the post or in any of the voices. A dead thinker's name is not a defence. This is usually empty and you should not invent something to fill it.

Do any of the voices agree with the post? A voice that agrees is doing no work.

What is the strongest objection the post does not deal with.

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
  "sources": [{{"title": "what it is", "url": "https://..."}}],
  "voices": [{{"thinker": "Karl Marx", "lived": "1818 to 1883",
              "argument": "how the argument runs, in your words, no quote marks, never first person",
              "quote": "only real searched words, or empty",
              "quote_url": "the link a search returned, or empty"}}],
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
