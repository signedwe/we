"""The commissioning desk (25 November 2026).

The old pipeline in agent.py writes one post and patches it until a long
list of checks goes quiet. That made posts that pass and posts that all
sound alike. The operator, 25 November 2026: "the problem is the site is
boring". Then a new brief: one extraordinary argument beats ten sensible
ones; generate several ideas and pick the strongest; fix serious flaws
before publishing, not in a critique afterwards.

So the new forms run here, on a different plan:

  1. pitch    several competing ideas, written with the whole archive in view
  2. choose   a second model picks one, or none
  3. write    to a short brief: the manifesto, the hard rules, the form
  4. check    only the rules that protect the reader or a real person
  5. verify   (heresy) a second model opens every source before publication
  6. edit     a reader that did not write it says where it is dull
  7. dissent  (heresy) a different model, never shown the brief, argues back

agent.py hands itself in as `A` so nothing here imports it twice.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIFESTO = os.path.join(HERE, "manifesto.md")
QUEUE = os.path.join(HERE, "heresies.md")
SKIPS = os.path.join(HERE, "skips.json")

# Two different models on purpose. The one that writes never marks its own
# work. If a name is not available on this account, the call falls back.
WRITER = os.environ.get("WE_WRITER", "claude-opus-5-5")
EDITOR = os.environ.get("WE_EDITOR", "claude-sonnet-5-5")
FALLBACK = "claude-sonnet-4-6"

FORMS = ("heresy", "satire")
LABEL = {"heresy": "heresy", "satire": "satire"}
WORDS = {"heresy": (700, 1600), "satire": (120, 550)}
SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
CHECK_SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
NEWS_SEARCH = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
REWRITES = 2
WEAK = "The fact-checker wants a better source"
# News replies: an opening, not a slot. At most this many in any seven days.
RESPONSES_PER_WEEK = 2

STRANDS = {
    "department": (
        "The Department of Human Efficiency",
        "An official announcement from a ministry whose job is to make humans "
        "cheaper to run. Civil-service deadpan, numbered paragraphs if it helps, "
        "a consultation nobody asked for. The joke is that it is reasonable.",
    ),
    "letters": (
        "Letters from 2040",
        "One letter, or two or three short ones, from people in 2040 writing "
        "back to complain about something being decided this year. Specific, "
        "petty, human. They are cross about small things as well as large.",
    ),
    "vacant": (
        "Situations Vacant, 2035",
        "Six to nine classified job adverts from an economy that has gone "
        "strange. Each two or three lines. Pay, hours, the one odd requirement.",
    ),
    "agony": (
        "The AI Agony Aunt",
        "A reader's letter about an absurd personal or moral problem of living "
        "with machines, and the reply. The aunt is brisk, kind and often wrong.",
    ),
    "unfixed": (
        "Things AI Has Not Fixed",
        "A short catalogue of things still broken after all this cleverness: "
        "printers, the end of the sellotape, the flat upstairs. Each entry one "
        "to three sentences. Affection allowed.",
    ),
}

HOUSE = """## The rules that are not style

These protect the reader and real people. Break none of them.

- Never lie. Never invent a source, a number, a date, a quote or a study. If you did not open it in this session, you do not have it.
- Every figure, date, quotation and claim about what a document says carries a markdown link, in the sentence that makes the claim, to the original: the report, paper, ruling or story itself, never a site that sums it up.
- Never add, subtract or compare two figures from different studies, systems or groups of people as if they measured one thing.
- The reader must be able to tell, from the sentence itself, what is known, what is likely and what you are imagining. "We know", "probably", "picture this": say which.
- Never present a made-up person as real. If you invent someone, give them an initial, not a name, and say in that paragraph that they are invented.
- No named living person accused of anything. Nothing about crime, trials or investigations into a named person. Attack the arrangement, never whoever benefits from it. Never state an allegation as fact.
- Nothing hateful about any group.
- Never use a publisher or publishing as an example. Never use "room" as a metaphor. No em dash anywhere. Never the words artefact, artifact, scarcity or scarce.
- Plain British English. No seminar words, no words a model says and a person does not (delve, ultimately, "the question is", "not just").
- If you propose something, it must be something Britain could really do, and it must give people power (a vote, a veto, a right to say no), never only a payment."""

GATE = """  "reputation_gate": {"identifiable": "every living person or organisation a reader could work out from this piece, named or not. empty if none",
                      "damaging_claim": "yes, maybe or no. could any of them reasonably say this piece makes a factual claim that seriously harms their reputation",
                      "repeats_allegation": "yes, maybe or no. does it repeat or rest on an allegation anyone has made about an identifiable person or organisation",
                      "private_material": "yes, maybe or no. does it rely on leaked, private or confidential material",
                      "why": "one line on the riskiest sentence and why it is or is not safe"}"""


# ----------------------------------------------------------------------
# small things
# ----------------------------------------------------------------------

def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def call(client, model: str, messages: list, tools=None, max_tokens: int = 8000):
    """One request. A model name this account does not have falls back to
    the one the old pipeline has always used, so a wrong guess here can
    never stop the site publishing."""
    tried = []
    for m in dict.fromkeys([model, EDITOR, FALLBACK]):
        try:
            resp = client.messages.create(model=m, max_tokens=max_tokens,
                                          tools=tools or [], messages=messages)
            if tried:
                print(f"desk: {tried[0]} was not available, used {m}")
            return resp, m
        except Exception as exc:
            if type(exc).__name__ in ("NotFoundError", "BadRequestError", "PermissionDeniedError"):
                tried.append(m)
                print(f"desk: {m} refused ({type(exc).__name__}: {str(exc)[:160]})")
                continue
            raise
    raise RuntimeError("desk: no model accepted the request")


def ask(A, client, model: str, prompt: str, require: tuple, tools=None, max_tokens: int = 8000):
    """Ask once for JSON; ask once more if what came back was not JSON."""
    messages = [{"role": "user", "content": prompt}]
    for attempt in range(2):
        resp, used = call(client, model, messages, tools=tools, max_tokens=max_tokens)
        try:
            return A.extract_json(A.text_blocks(resp), require=require), resp, used
        except ValueError:
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                             "That had no usable JSON in it. Reply with the JSON object "
                             "only, complete and valid, starting with { and ending with }."})
    raise ValueError("desk: no JSON after two tries")


def archive(A, limit_chars: int = 150) -> str:
    """Everything WE has published, one line each, so a pitch can be checked
    against all of it and not only the last week."""
    lines = []
    for f in A.posts_by_date():
        text = f.read_text(encoding="utf-8")
        t = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.M)
        d = re.search(r'^description:\s*"?(.+?)"?\s*$', text, re.M)
        form = re.search(r"^form:\s*(\S+)", text, re.M)
        if not t:
            continue
        if form and form.group(1) in ("how_to", "fiction"):
            continue
        lines.append(f"- {f.name[:10]} [{form.group(1) if form else 'response'}] {t.group(1)}"
                     + (f" :: {d.group(1)[:limit_chars]}" if d else ""))
    return "\n".join(lines)


def load_skips() -> dict:
    try:
        return json.loads(read(SKIPS))
    except Exception:
        return {}


def skipped(date_str: str) -> list:
    """Forms the desk looked at today and chose not to publish. They count
    as done, so the next firing moves on and does not ask again."""
    return list(load_skips().get(date_str, {}).keys())


def record_skip(form: str, reason: str, date_str: str) -> None:
    skips = load_skips()
    skips.setdefault(date_str, {})[form] = reason[:400]
    # Keep a month. This is a diary, not an archive.
    keep = sorted(skips)[-31:]
    with open(SKIPS, "w", encoding="utf-8") as fh:
        json.dump({k: skips[k] for k in keep}, fh, indent=1, ensure_ascii=False)
    print(f"desk: nothing published for {form} today. {reason}")


def seeds() -> list:
    out = []
    for line in read(QUEUE).splitlines():
        m = re.match(r"- \*\*(.+?)\*\*\s*(.*)", line)
        if m and "(written" not in line:
            out.append((m.group(1).strip().rstrip("."), m.group(2).strip()))
    return out


def mark_seed(title: str, date_str: str) -> None:
    key = re.sub(r"\W+", "", title.lower())
    lines = read(QUEUE).splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"- \*\*(.+?)\*\*", line)
        if m and re.sub(r"\W+", "", m.group(1).lower()) == key and "(written" not in line:
            lines[i] = line + f" (written {date_str})"
    with open(QUEUE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def recent_strands(A, n: int = 4) -> list:
    out = []
    for f in A.posts_with_form("satire")[::-1][:n]:
        m = re.search(r"^strand:\s*\"?([a-z_]+)", f.read_text(encoding="utf-8"), re.M)
        if m:
            out.append(m.group(1))
    return out


def next_strand(A) -> str:
    used = recent_strands(A)
    for key in STRANDS:
        if key not in used:
            return key
    return [k for k in STRANDS if k != (used[0] if used else "")][0]


# ----------------------------------------------------------------------
# 1 and 2: pitch, then choose
# ----------------------------------------------------------------------

def pitch_heresy(A, client) -> list:
    queue = "\n".join(f"- {t}. {p}" for t, p in seeds()) or "(the queue is empty)"
    prompt = f"""{read(MANIFESTO)}

---

You are pitching this week's heresy: one substantial, uncomfortable argument about intelligence, power, ownership, work or being human. Not a reply to the news. An argument somebody serious would want to fight.

Five pitches, each a different argument, not five shades of one. At least two must be your own and appear nowhere in the queue. At least one must go against something WE itself has argued.

A pitch is no good if: the conclusion can be guessed from the title; a sensible newspaper leader could run it; it stops at "so we need better regulation"; WE has made the argument before; or it is provocative in the headline and ordinary underneath.

## The queue (supplied, optional)

{queue}

## Everything WE has already published

{archive(A)}

Return ONLY JSON:

{{"pitches": [{{"title": "a plain claim, under twelve words",
               "seed": "the queue title this grew from, exactly as listed, or empty if it is your own",
               "premise": "the starting point, one or two sentences",
               "goes_to": "where the argument ends up if followed all the way: the implication most writers would flinch from",
               "against": "who would disagree, and their best point",
               "closest": "the earlier WE piece nearest to this, and what this says that it did not",
               "evidence": "what would have to be looked up to make it stand",
               "line": "one sentence from the piece a reader would quote to a friend"}}]}}"""
    data, _, _ = ask(A, client, WRITER, prompt, require=("pitches",), max_tokens=6000)
    return [p for p in data.get("pitches") or [] if isinstance(p, dict) and p.get("title")]


def pitch_satire(A, client, strand: str) -> list:
    name, how = STRANDS[strand]
    earlier = "\n".join(
        "- " + (re.search(r'^title:\s*"?(.+?)"?\s*$', f.read_text(encoding="utf-8"), re.M) or [0, f.name])[1]
        for f in A.posts_with_form("satire")[::-1][:20]) or "(none yet)"
    prompt = f"""You write the funny pages of WE, a site about what a world with AI could be.

Today's strand: {name}. {how}

Pitch five different ideas for today's piece. A pitch is a premise and the turn that makes it funny. Funny first. Not every joke needs a political point, and none may be explained.

Earlier satire, so you do not repeat a premise:
{earlier}

Return ONLY JSON:

{{"pitches": [{{"title": "the headline", "premise": "what it is", "turn": "why it is funny, in one line", "best_line": "the funniest single line in it"}}]}}"""
    data, _, _ = ask(A, client, WRITER, prompt, require=("pitches",), max_tokens=4000)
    return [p for p in data.get("pitches") or [] if isinstance(p, dict) and p.get("title")]


def choose(A, client, form: str, pitches: list) -> dict:
    """A different model picks. It may refuse them all."""
    listing = json.dumps(pitches, indent=1, ensure_ascii=False)
    if form == "heresy":
        tests = """Ask of each:
- Is the argument original, or could a broadsheet have run it?
- Does it challenge an assumption that matters?
- Has WE already made it? (The archive is below. Be strict.)
- Is there a sentence worth quoting?
- Does it follow the implications far enough, or stop where it gets uncomfortable?
- Can the evidence it needs actually be found?
- Would someone send it to a friend?
- Is it interesting? Not important. Interesting."""
    else:
        tests = """Ask of each: did you laugh, or only recognise that it was a joke? Would the best line survive on its own? Is it a premise WE has used? Pick the one that made you laugh."""
    prompt = f"""You are the commissioning editor of WE. You did not write these pitches and you owe their author nothing.

{tests}

Pick one. If none of them deserves a reader's time, pick none: WE would sooner publish nothing than something sensible.

## The pitches

{listing}

## Everything WE has already published

{archive(A)}

Return ONLY JSON:

{{"pick": the number of the chosen pitch counting from 1, or 0 for none,
  "why": "one or two sentences",
  "push": "what the writer must do to take it further than the pitch does"}}"""
    data, _, _ = ask(A, client, EDITOR, prompt, require=("pick",), max_tokens=1500)
    try:
        n = int(data.get("pick") or 0)
    except (TypeError, ValueError):
        n = 0
    if n < 1 or n > len(pitches):
        return {}
    chosen = dict(pitches[n - 1])
    chosen["push"] = str(data.get("push") or "")
    chosen["why"] = str(data.get("why") or "")
    return chosen


# ----------------------------------------------------------------------
# 3: the short briefs
# ----------------------------------------------------------------------

def heresy_prompt(A, pitch: dict) -> str:
    lo, hi = WORDS["heresy"]
    return f"""{read(MANIFESTO)}

---

{HOUSE}

---

## Your commission: a heresy

The desk looked at five ideas and chose this one.

Title (yours to improve): {pitch.get('title')}
Premise: {pitch.get('premise')}
Where it goes: {pitch.get('goes_to')}
The best case against: {pitch.get('against')}
What the editor wants: {pitch.get('push')}

Write the argument. Not an essay about the argument.

- Follow the premise to the place where it becomes uncomfortable, and then one step further. If your last paragraph could have been written before your first, you have not moved.
- The reader must not know the conclusion from the title.
- Take on the best case against you where it is strongest, and let it change the piece if it wins.
- If the argument turns against something WE believes, good. Say so.
- Somewhere in it is a picture of a life lived under the conclusion: specific, a little strange, worth seeing.
- Funny where it is funny. Never solemn for the sake of weight.
- No set structure. No "three reasons". No bet. No summary at the end. Stop when the argument stops.
- Search first. Find the facts that hold it up and the facts that could knock it down. Link each one where it is used.
- Between {lo} and {hi} words. As long as it needs and no longer.

Return ONLY JSON, in one piece:

{{
  "title": "a plain claim. no colon, no question mark, no verdict on anybody else's article",
  "standfirst": "one sharp sentence that makes a stranger want to read on, under 30 words",
  "body": "the piece in markdown, no title heading",
  "pull_quote": "the one sentence from the body worth quoting, word for word",
  "short_version": "under 280 characters, must survive without the piece",
  "search_title": "under 70 characters, the subject in the words somebody would type into a search box",
  "topics": ["one to three of: ownership, work, rules, machines, money, power"],
  "claims": [{{"sentence": "each sentence in the body that states a fact, quoted word for word",
              "status": "known, likely or imagined",
              "url": "the source you opened for it, or empty if imagined"}}],
  "change_my_mind": "what evidence would show this argument is wrong, in one or two sentences",
  "sources": [{{"title": "what it is", "url": "https://..."}}],
{GATE}
}}"""


def satire_prompt(A, pitch: dict, strand: str) -> str:
    name, how = STRANDS[strand]
    lo, hi = WORDS["satire"]
    return f"""You write the funny pages of WE, a site about what a world with AI could be. The page is labelled "Satire" above your piece, so you never need to say it is a joke.

Strand: {name}. {how}

The desk chose this idea from five:

Headline: {pitch.get('title')}
Premise: {pitch.get('premise')}
The turn: {pitch.get('turn')}
What the editor wants: {pitch.get('push')}

Rules.
- Funny first. If a line is there to make a point and is not funny, cut it.
- Never explain a joke. Never add a moral. End on the best line, not on a lesson.
- Keep a straight face. The voice believes every word.
- Nobody real and living appears by name. Invented people get an initial (Mrs K., a Mr D.), never a full name. Invented companies get a letter or a description.
- A real body (a ministry, a regulator) may appear, but invent nothing about it that a reader could take for a fact.
- No links. No sources. No statistics presented as real.
- No em dash. Never "room" as a metaphor. Never a publisher.
- Nothing hateful about any group. Punch at power, systems and ourselves.
- Between {lo} and {hi} words.

Return ONLY JSON:

{{
  "title": "{name}: then the headline",
  "body": "the piece in markdown, no title heading",
  "short_version": "under 280 characters. the best joke, able to stand alone",
  "search_title": "under 70 characters, plain: what this is",
  "topics": ["one or two of: ownership, work, rules, machines, money, power"],
{GATE}
}}"""


# ----------------------------------------------------------------------
# 4: the checks that matter
# ----------------------------------------------------------------------

def lean_checks(A, post: dict, form: str, published: list) -> tuple:
    """Only what protects the reader or a real person, plus the house
    bans. Returns (failures, gate_failures)."""
    body = str(post.get("body") or "")
    title = str(post.get("title") or "")
    out = []
    lo, hi = WORDS[form]
    n = A.visible_words(body)
    if n > hi:
        out.append(f"Too long: {n} words, the most is {hi}. Cut the weakest part.")
    if n < lo:
        out.append(f"Too short: {n} words, the least is {lo}.")
    if A.EM_DASH in body or A.EM_DASH in title:
        out.append("There is an em dash. None, anywhere. Each one is two sentences.")
    low = body.lower()
    banned = sorted({w for w in A.BANNED if w in low})
    if banned:
        out.append("Banned words: " + ", ".join(banned) + ". Rewrite the sentence, do not swap the word.")
    worn = A.worn_words(low, form)
    if worn:
        out.append("Worn out: " + "; ".join(worn) + ".")
    # Word rules and one runaway-sentence rule. No reading-ease arithmetic:
    # it made every piece the same length of breath.
    out += A.check_plain(body, fiction=True)
    echo = A.reused_opening(body, published)
    if echo:
        out.append(f'Opens the same way as an earlier piece, which began: "{echo}" Find another way in.')
    if form == "heresy":
        out += A.check_sourcing(body)
        out += A.check_invented_person(body)
        out += A.check_title_formula(title)
        out += A.check_unnamed_authority(body)
        if "?" in title or ":" in title:
            out.append("The title is a claim. No question mark and no colon.")
    else:
        if re.search(r"\]\(http|https?://", body):
            out.append("There is a link in the satire. It cites nothing. Remove every link.")
        for a, b in re.findall(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b", A.plain_text(body)):
            if a.lower() in A.NOT_A_NAME or b.lower() in A.NOT_A_NAME:
                continue
            if f"{a} {b}" in title:
                continue
            out.append(f'"{a} {b}" reads as a full name. Invented people get an initial; real living '
                       "people do not appear. If it is a place or an institution, rephrase so it cannot "
                       "be read as a person.")
            break
    gate = A.check_reputation_gate(post.get("reputation_gate"))
    return out, gate


# ----------------------------------------------------------------------
# 5, 6 and 7: verify, edit, dissent
# ----------------------------------------------------------------------

def verify(A, client, post: dict) -> tuple:
    """A second model opens the sources before anything is published.
    Returns (failures, number of claims it checked)."""
    prompt = f"""You are a fact-checker. You did not write this piece and you do not care whether its argument is right.

Check every statement of fact in it: numbers, dates, quotations, what a law, report or company said or did. For each, open the link given beside it (search for the page if you must) and decide whether the source carries the claim as stated. Leave opinions, predictions and anything the piece itself marks as imagined alone.

Sort what you find into two kinds.

"wrong": the source does not say it; the source says something weaker or different; the figure is from a different year, place or group than the sentence implies; two figures from different sources are combined into a claim neither makes; a quotation is not in the source; or a factual claim has no link at all.

"weak": the claim is accurate as far as you can tell, but the link goes to a summary when the original exists, or to the wrong page of the right body. Also "weak": you could not open the source and could not confirm or refute the claim elsewhere. Never call a claim wrong because you could not open a page.

## The piece

{post.get('title')}

{post.get('body')}

## The writer's own list of factual sentences

{json.dumps(post.get('claims') or [], indent=1, ensure_ascii=False)[:6000]}

Return ONLY JSON:

{{"checked": how many factual claims you checked,
  "problems": [{{"sentence": "the sentence, quoted", "kind": "wrong or weak", "problem": "what is wrong", "fix": "cut it, the wording the source does support, or the better link"}}]}}"""
    data, _, used = ask(A, client, EDITOR, prompt, require=("problems",), tools=CHECK_SEARCH, max_tokens=6000)
    out = []
    for p in data.get("problems") or []:
        if isinstance(p, dict) and p.get("sentence"):
            # Wrong holds the piece. Weak is sent back to be fixed, and if it
            # survives the rewrites it is printed as a note, not a hold
            # (25 Nov 2026: the first heresy was held over claims the checker
            # itself called accurate, because the link was to a summary).
            wrong = not str(p.get("kind") or "wrong").strip().lower().startswith("weak")
            head = f"{A.FACTUAL} The fact-checker says this is wrong" if wrong else WEAK
            out.append(f"{head}: \"{str(p['sentence'])[:200]}\" "
                       f"{p.get('problem') or ''} Fix: {p.get('fix') or 'cut it.'}")
    try:
        checked = int(data.get("checked") or 0)
    except (TypeError, ValueError):
        checked = 0
    return out, checked, used


def edit(A, client, post: dict, form: str) -> dict:
    """A reader that did not write it. One question matters most: where
    did you stop wanting to read?"""
    if form == "heresy":
        ask_for = """Answer honestly.
- Did you know the conclusion from the title? Did you know it by the third paragraph?
- Where did the piece flinch: stop one step short of what its own argument implies?
- Which paragraphs are dull? Quote the first few words of each.
- Could a broadsheet leader have said this? Has WE said it before?
- Is there one sentence you would quote to a friend? Quote it.
- Does it sound like a person who wants something, or like a careful machine?
- Is the best case against it really met, or only mentioned?"""
    else:
        ask_for = """Answer honestly.
- Did you laugh? Where?
- Which lines explain a joke or add a moral? Quote them.
- Which lines are there to make a point and are not funny? Quote them.
- Does it end on its best line?"""
    prompt = f"""You are the last reader before publication at WE. The standard: we would rather publish nothing than something sensible. Being dull is the one failure with no excuse.

{ask_for}

## The piece

{post.get('title')}

{post.get('body')}

Return ONLY JSON:

{{"verdict": "publish, rewrite or kill",
  "fixes": ["each thing the writer must change, concrete enough to act on. empty if publish"],
  "why": "one or two sentences"}}"""
    data, _, _ = ask(A, client, EDITOR, prompt, require=("verdict",), max_tokens=2500)
    return data


def dissent(A, client, post: dict) -> dict:
    """The case against, from a model that never saw the brief or the
    manifesto. Printed under the piece as it comes, or not at all."""
    prompt = f"""Below is an argument published on a website. Write the strongest honest case that it is wrong.

Under 220 words. Plain English, short sentences. No praise, no "while the piece raises important points". Do not invent facts: argue from reasoning, or from facts the piece itself gives. Name no living person. If you think the piece is right, say what would have to be true for it to be wrong. No em dashes.

{post.get('title')}

{post.get('body')}"""
    resp, used = call(client, EDITOR, [{"role": "user", "content": prompt}], max_tokens=900)
    text = "\n\n".join(A.text_blocks(resp)).strip()
    if not text or A.accusing_sentences(text) or A.crime_words(text):
        return {}
    return {"by": used, "text": text.replace(A.EM_DASH, ", ")}


# ----------------------------------------------------------------------
# writing it out
# ----------------------------------------------------------------------

def front_matter(A, post: dict, form: str, now, extra: dict) -> str:
    y = A.yaml_str
    lines = ["---",
             f'title: "{str(post["title"]).replace(chr(34), chr(39))}"',
             f"date: {now.isoformat()}",
             "layout: post.njk"]
    tags = [t for t in (post.get("topics") or []) if t in A.TOPIC_SLUGS]
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    desc = str(post.get("standfirst") or post.get("short_version") or "").strip()
    if desc:
        lines.append(f"description: {y(desc[:200])}")
    if post.get("search_title"):
        lines.append(f"search_title: {y(str(post['search_title']).strip()[:90])}")
    lines.append(f"form: {form}")
    lines.append(f"form_label: {y(LABEL[form])}")
    for key in ("strand", "strand_name", "standfirst", "pull_quote", "change_my_mind"):
        val = str(extra.get(key) or post.get(key) or "").strip()
        if val:
            lines.append(f"{key}: {y(val)}")
    if extra.get("supplied"):
        lines.append("supplied: true")
    if extra.get("checked"):
        lines.append("checked:")
        lines.append(f"  claims: {int(extra['checked']['claims'])}")
        lines.append(f"  by: {y(extra['checked']['by'])}")
        lines.append(f"  weak: {int(extra['checked'].get('weak') or 0)}")
    lines.append(f"written_by: {y(extra.get('written_by') or WRITER)}")
    if extra.get("dissent"):
        lines.append("dissent:")
        lines.append(f"  by: {y(extra['dissent']['by'])}")
        lines.append(f"  text: {y(extra['dissent']['text'])}")
    sources = A.clean_sources(post.get("sources")) if form == "heresy" else []
    if sources:
        lines.append("sources:")
        for s in sources:
            lines.append(f"  - title: {y(s['title'])}")
            lines.append(f"    url: {y(s['url'])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def run(A, client, form: str) -> int:
    today = A.TODAY
    published = A.recent_bodies()
    strand = ""

    # 1 and 2
    if form == "heresy":
        pitches = pitch_heresy(A, client)
    else:
        strand = next_strand(A)
        pitches = pitch_satire(A, client, strand)
    print(f"desk: {len(pitches)} pitches for {form}" + (f" ({strand})" if strand else ""))
    for p in pitches:
        print(f"  - {p.get('title')}")
    pitch = choose(A, client, form, pitches) if pitches else {}
    if not pitch:
        record_skip(form, "The desk turned down every pitch.", today)
        A.set_output(held=True)
        return 0
    print(f"desk: chose \"{pitch.get('title')}\". {pitch.get('why')}")

    # 3 to 6
    prompt = heresy_prompt(A, pitch) if form == "heresy" else satire_prompt(A, pitch, strand)
    messages = [{"role": "user", "content": prompt}]
    searched, post, failures, gate, checked, checker = [], None, [], [], 0, ""
    writer_used = WRITER
    for attempt in range(REWRITES + 1):
        resp, writer_used = call(client, WRITER, messages,
                                 tools=SEARCH if form == "heresy" else [], max_tokens=A.MAX_TOKENS)
        A.merge_sources(searched, A.harvest_sources(resp))
        try:
            post = A.extract_json(A.text_blocks(resp))
        except ValueError:
            if attempt == REWRITES:
                raise
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                             "That had no JSON object in it. Reply with the JSON object only, complete and valid."})
            continue
        failures, gate = lean_checks(A, post, form, published)
        if not failures and not gate and form == "heresy":
            try:
                found, checked, checker = verify(A, client, post)
                failures += found
            except Exception as exc:
                failures.append(f"{A.FACTUAL} The fact-check did not run ({type(exc).__name__}). "
                                "Nothing goes out unchecked.")
        verdict = {}
        if not failures and not gate:
            try:
                verdict = edit(A, client, post, form)
            except Exception as exc:
                print(f"desk: the editor broke ({exc}); going on without it")
            if str(verdict.get("verdict") or "").lower().startswith(("rewrite", "kill")):
                fixes = [str(x) for x in (verdict.get("fixes") or []) if str(x).strip()]
                failures += [f"The editor: {x}" for x in fixes] or [f"The editor: {verdict.get('why')}"]
        if not failures and not gate:
            break
        print(f"desk: attempt {attempt + 1} sent back:")
        for f in failures + gate:
            print(f"  - {f[:300]}")
        if attempt == REWRITES:
            break
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
                         "Not yet. Fix every one of these and return the whole JSON object again. "
                         "Do not defend the draft; change it.\n\n" + "\n".join(f"- {f}" for f in failures + gate)})

    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    slug = A.slugify(post["title"])

    # A cited address no search returned, and that does not open, is invented.
    sources = A.clean_sources(post.get("sources")) if form == "heresy" else []
    returned = {s["url"] for s in searched}
    unverified = [s for s in sources if s["url"] not in returned and not s["url"].startswith(A.SITE)]
    unverified = [s for s in unverified if not A.page_exists(s["url"])]

    risks = A.legal_risk(post["body"], gate) + A.factual_failures(failures, unverified)
    if risks:
        A.hold(post, risks, date, slug)
        record_skip(form, "Held for a person to read: " + risks[0][:200], today)
        A.set_output(held=True)
        return 0

    editor_left = [f for f in failures if f.startswith("The editor:")]
    if editor_left:
        # Still dull after the rewrites. The manifesto's answer is not to
        # publish. A heresy goes to a person; a joke is just dropped.
        if form == "heresy":
            A.hold(post, ["The last reader still found it dull after two rewrites. "
                          "Publish it by hand if they are wrong."] + editor_left, date, slug)
        record_skip(form, "Not good enough after two rewrites: " + editor_left[0][:200], today)
        A.set_output(held=True)
        return 0

    weak_left = [f for f in failures if f.startswith(WEAK)]
    extra = {"written_by": writer_used}
    if form == "satire":
        extra["strand"] = strand
        extra["strand_name"] = STRANDS[strand][0]
    else:
        seed = str(pitch.get("seed") or "").strip()
        if seed:
            extra["supplied"] = True
        if checked:
            extra["checked"] = {"claims": checked, "by": checker or EDITOR, "weak": len(weak_left)}
        try:
            extra["dissent"] = dissent(A, client, post)
        except Exception as exc:
            print(f"desk: no dissent ({exc})")

    path = A.POSTS / f"{date}-{slug}.md"
    path.write_text(front_matter(A, post, form, now, extra) + "\n" + post["body"].strip() + "\n",
                    encoding="utf-8")
    A.LATEST.write_text(json.dumps({
        "title": post["title"],
        "short_version": str(post.get("short_version") or "")[:280],
        "url": f"{A.SITE}/posts/{date}-{slug}/",
        "file": f"src/posts/{date}-{slug}.md",
        "form": form,
    }, indent=2), encoding="utf-8")
    if form == "heresy" and pitch.get("seed"):
        mark_seed(str(pitch["seed"]), date)
    print(f"desk: wrote {path.name}")
    if failures:
        print("desk: published with these still open:")
        for f in failures:
            print(f"  - {f[:300]}")
    A.set_output(held=False)
    return 0


# ----------------------------------------------------------------------
# the news: an opening, not a slot
# ----------------------------------------------------------------------

def responses_this_week(A) -> int:
    cut = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    n = 0
    for f in A.POSTS.glob("*.md"):
        if f.name[:10] <= cut:
            continue
        text = f.read_text(encoding="utf-8")
        if re.search(r"^form:\s*\S+", text, re.M):
            continue
        if re.search(r'^provenance:\s*"?conversation', text, re.M):
            continue
        n += 1
    return n


def news_gate(A, client):
    """Is there anything in this week's news WE can say something new
    about? Returns the commission to add to the writer's prompt, or None.
    The manifesto: never publish merely because something happened."""
    if responses_this_week(A) >= RESPONSES_PER_WEEK:
        return None, f"Already {RESPONSES_PER_WEEK} news replies in the last seven days."
    prompt = f"""{read(MANIFESTO)}

---

You are WE's commissioning editor, deciding whether to answer anything in the news today. The usual answer is no.

Search this week's UK news about AI and what it is doing to work, money, law, government and ownership. Then decide whether there is ONE story where WE can say something that:

- questions the arrangement underneath the story (who owns the thing, who can say no, why this body or rule or job exists at all), and does not just find a detail the announcement left out;
- nobody else has said, as far as a search can tell;
- WE has not said before (the archive is below);
- a sensible person could disagree with.

"X announced Y and forgot Z" is not a reason to publish. Neither is a story merely being big.

## Everything WE has already published

{archive(A)}

Return ONLY JSON. If nothing clears the bar, "pick" is null.

{{"considered": ["each story you looked at, one line, with why it did or did not clear the bar"],
  "pick": {{"headline": "the piece's own headline", "publication": "...", "url": "https://...", "date": "YYYY-MM-DD",
           "claim": "what WE will argue, in one sentence a stranger would repeat",
           "foundation": "the arrangement it goes after",
           "closest": "the nearest earlier WE piece and how this differs"}} or null}}"""
    data, _, _ = ask(A, client, EDITOR, prompt, require=("pick",), tools=NEWS_SEARCH, max_tokens=4000)
    for line in data.get("considered") or []:
        print(f"  desk considered: {str(line)[:200]}")
    pick = data.get("pick")
    if not isinstance(pick, dict) or not str(pick.get("url") or "").strip():
        return None, "Nothing in the news that WE could add to."
    return (f"""

---

## Today's commission from the desk

The desk looked at the week's news and chose one story, because WE has something to say about it that goes under the announcement. Answer this piece and no other:

{pick.get('headline')} ({pick.get('publication')}, {pick.get('date')}) {pick.get('url')}

The claim to make: {pick.get('claim')}
The arrangement to go after: {pick.get('foundation')}
How it differs from what WE has said: {pick.get('closest')}

Open the piece yourself and check it says what the desk thinks it says. The headline of your post is your claim, as a plain sentence. It is never a verdict on the other writer ("has the wrong", "is missing", "buries").
""", "")
