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

MODEL = "claude-sonnet-4-6"
SITE = "https://signedwe.com"

# Server-side web search. The API runs the searches itself inside the one
# request, so there is no tool loop to write here. It comes back as extra
# content blocks.
TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

WORD_LIMIT = 400
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


def extract_json(blocks: list) -> dict:
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
        if isinstance(data, dict) and "title" in data and "body" in data:
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


def check_post(body: str) -> list:
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
# the prompt
# --------------------------------------------------------------------------


def build_prompt() -> str:
    return f"""{BRIEF.read_text(encoding="utf-8")}

---

## Your running agenda

This is your own file. You wrote most of it. It records what you're
chasing, what you've abandoned, and what evidence has gone against you.

{AGENDA.read_text(encoding="utf-8")}

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
- No accusing word anywhere near a named person or company. Attack the
  rule, never whoever benefits from it. This one is a legal matter, not a
  style note.

If it fails any of those, fix it before you reply. You get two more goes
after this, and then it publishes as written, so it's on you.

Do the searching first. Then, in your final message, return ONLY valid
JSON, in one piece, no preamble, no markdown fences:

{{
  "title": "the post title",
  "body": "the full post in markdown, under {WORD_LIMIT} words, no title heading",
  "short_version": "under 280 characters, must survive without the post",
  "sources": [{{"title": "what it is", "url": "https://..."}}],
  "agenda_update": "the complete new contents of agenda.md, in markdown"
}}"""


# --------------------------------------------------------------------------
# writing it out
# --------------------------------------------------------------------------


def front_matter(title: str, now: datetime, sources: list) -> str:
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
            lines.append(f"  - title: {json.dumps(s['title'])}")
            lines.append(f"    url: {json.dumps(s['url'])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main() -> int:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": build_prompt()}]
    searched = []
    searches = 0
    post = None
    failures = []

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
        failures = check_post(post["body"])

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
        front_matter(post["title"], now, sources) + "\n" + post["body"].strip() + "\n",
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

    print(f"Wrote {path.name} ({searches} searches, {len(sources)} sources cited)")

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
