"""WE writes one history essay a week, and a second machine checks it first.

The operator's instruction (23 September 2026): a History section of
long-form essays on the history of AI and the ideas that led to it, at the
level of a review essay written by an academic for a popular audience,
accurate, with real footnotes, no invention, and each one peer reviewed
before publication. Then: "And they are published weekly."

The shape of a run:

1. Stand down if an essay was published in the last six days.
2. Take the first subject in agent/history-subjects.md not marked done.
3. The writer (with web search) produces the essay as JSON.
4. Local checks: word rules, worn images, footnote plumbing, length.
5. The reviewer, a fresh conversation with no sight of the drafts, is given
   the essay and its source URLs, opens them, checks every quotation and
   claim, and reports JSON findings.
6. Errors and unsupported claims go back to the writer; the corrected essay
   is reviewed again. Two review passes at most.
7. If errors survive the last pass, the essay is held (written to
   agent/held/, nothing committed). Otherwise it is written to src/history/
   with the review published at its foot, the subject is marked done, and
   latest.json points at it for the announce step.

Usage:
    python agent/history.py            # the weekly run
    DRAFT=1 python agent/history.py    # writes to agent/held/ instead
"""

import json
import os
import pathlib
import re
import sys
from datetime import datetime, timedelta, timezone

import anthropic

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import agent  # noqa: E402  (worn_words, text_blocks, extract_json, slugify)
from plain import check_plain  # noqa: E402

ROOT = agent.ROOT
HIST = ROOT / "src" / "history"
BRIEF = ROOT / "agent" / "history-brief.md"
SUBJECTS = ROOT / "agent" / "history-subjects.md"
HELD = ROOT / "agent" / "held"
LATEST = ROOT / "agent" / "latest.json"
SITE = agent.SITE
DRAFT = bool(os.environ.get("DRAFT"))

# The writer gets the same model as the daily posts. An essay of this
# length may deserve the larger model; change it here and nowhere else.
MODEL = agent.MODEL
MAX_TOKENS = 32000

WRITER_TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 20}]
# The reviewer needs to open pages, not skim snippets, because a quotation
# is checked word for word. web_fetch is a beta server tool; if the beta
# is refused the reviewer falls back to search alone and says so.
FETCH_BETA = "web-fetch-2025-09-10"
REVIEW_TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 8},
    {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 30},
]

MIN_WORDS, MAX_WORDS = 2500, 4500
MIN_NOTES = 8
REVIEW_PASSES = 2

REVIEW_BY = (
    "A second machine, with no part in the writing and no sight of the "
    "drafts, was given the finished essay and every source it cites. It "
    "opened each source, checked every direct quotation word for word and "
    "every footnoted and unfootnoted claim, and reported. Where it found an "
    "error the essay was corrected and reviewed again before publication."
)


# ---------------------------------------------------------------- helpers


def create(client, beta: bool = False, **kw):
    """One request, streamed. The SDK refuses a plain request whose
    max_tokens could take over ten minutes, and an essay needs the room."""
    api = client.beta.messages if beta else client.messages
    with api.stream(**kw) as stream:
        return stream.get_final_message()

def today() -> datetime:
    return datetime.now(timezone.utc)


def published_this_week():
    cutoff = (today() - timedelta(days=6)).strftime("%Y-%m-%d")
    for p in sorted(HIST.glob("*.md")):
        if p.name[:10] >= cutoff:
            return p
    return None


def next_subject():
    done, todo = [], []
    for line in SUBJECTS.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- "):
            continue
        text = line[2:].strip()
        (done if "[done" in text else todo).append(text)
    if not todo:
        raise SystemExit("history-subjects.md has no subject left. Add some.")
    return todo[0], [re.sub(r"\s*\[done.*\]$", "", d) for d in done]


def mark_done(subject: str, filename: str) -> None:
    lines = SUBJECTS.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        if line.startswith("- ") and line[2:].strip() == subject:
            line = f"- {subject} [done {today().strftime('%Y-%m-%d')} {filename}]"
        out.append(line)
    SUBJECTS.write_text("\n".join(out) + "\n", encoding="utf-8")


def plain_body(body: str) -> str:
    """The essay without the notes block or any tag, for the word checks."""
    body = body.split('<div class="notes">')[0]
    return re.sub(r"<[^>]+>", "", body)


def note_urls(body: str) -> list:
    notes = body.split('<div class="notes">', 1)[-1]
    return list(dict.fromkeys(re.findall(r'href="(https?://[^"]+)"', notes)))


def check_essay(body: str) -> list:
    """Everything that can be checked without reading a source."""
    failures = []
    text = plain_body(body)
    words = len(text.split())
    if words < MIN_WORDS:
        failures.append(f"Too short: {words} words. The form is {MIN_WORDS} to {MAX_WORDS}.")
    if words > MAX_WORDS:
        failures.append(f"Too long: {words} words. The form is {MIN_WORDS} to {MAX_WORDS}.")
    if agent.EM_DASH in body:
        failures.append("Em dashes. None, anywhere, including the notes. Use a comma, a colon, or a full stop.")
    # The word rules only. Sentence arithmetic is off for this form; a
    # sentence may run long here when it earns it.
    for f in check_plain(text, fiction=True):
        if "sentence runs" not in f and "sentences run" not in f:
            failures.append(f)
    worn = agent.worn_words(text.lower(), "history")
    if worn:
        failures.append("Worn out: " + "; ".join(worn) + ".")
    # Footnote plumbing.
    refs = re.findall(r'<a href="#fn(\d+)">', body)
    notes = re.findall(r'<li id="fn(\d+)">', body)
    if len(notes) < MIN_NOTES:
        failures.append(f"Only {len(notes)} notes. Real footnotes, at least {MIN_NOTES}; a claim a reader could check carries one.")
    missing = sorted({r for r in refs if r not in notes}, key=int)
    if missing:
        failures.append("Footnote markers with no note: " + ", ".join(missing) + ".")
    unused = sorted({n for n in notes if n not in refs}, key=int)
    if unused:
        failures.append("Notes never referred to: " + ", ".join(unused) + ".")
    ids = re.findall(r'id="(fnref[0-9a-z]+)"', body)
    if len(ids) != len(set(ids)):
        failures.append("Duplicate fnref ids. A note used twice gets a second id (fnref3b) pointing at the same #fn3.")
    notes_block = body.split('<div class="notes">', 1)[-1]
    for li in re.findall(r"<li id=\"fn\d+\">(.*?)</li>", notes_block, flags=re.S):
        if 'href="http' not in li:
            failures.append("A note with no link: " + re.sub(r"<[^>]+>", "", li)[:80] + ". Every note is a page a reader can open.")
            break
    return failures


def review_prompt(essay: dict) -> str:
    urls = "\n".join(note_urls(essay["body"]))
    return (
        "You are the peer reviewer for a long-form history essay written for "
        "a popular audience. You had no part in writing it. Your job is to "
        "stop it being published if it contains errors. The rule of the site "
        "is: no lies or made up stuff; every footnote real and supporting the "
        "sentence it hangs from; every quotation word for word.\n\n"
        "Do this:\n"
        "1. Fetch every source URL listed below. If a fetch fails, say so and "
        "search for the same fact elsewhere.\n"
        "2. For EVERY footnoted claim and EVERY direct quotation (text in "
        "double quotes), check it against the source it cites. Quotations "
        "must be word for word; report any deviation, giving the source's "
        "exact wording.\n"
        "3. Check the unfootnoted factual claims too, searching where needed: "
        "dates, ages, titles, places, who said what, what a machine could do.\n"
        "4. Look for invented colour presented as fact, anachronism, and any "
        "interpretation presented as a source's content rather than the "
        "essay's reading.\n"
        "5. Judge whether the argument is defensible and marked as "
        "interpretation where it goes beyond the sources.\n\n"
        "Report as JSON only, nothing else:\n"
        '{"verdict": "PUBLISH" | "PUBLISH WITH CORRECTIONS" | "DO NOT PUBLISH",\n'
        ' "summary": "two or three sentences",\n'
        ' "findings": [{"claim": "the exact words in the essay", '
        '"finding": "what the source says, with the source named, or confirmed", '
        '"severity": "error" | "unsupported" | "quibble" | "confirmed", '
        '"action": "what to change, or none"}]}\n'
        "Include a finding for every direct quotation (confirmed or not) and "
        "for every error or unsupported claim. Do not pad with confirmations "
        "of trivial things beyond the quotations. Be exact and be hard; a "
        "reviewer who waves things through is useless here.\n\n"
        f"SOURCE URLS\n{urls}\n\n"
        f"TITLE\n{essay['title']}\n\n"
        f"ESSAY\n{essay['body']}\n"
    )


def run_review(client, essay: dict) -> dict:
    prompt = review_prompt(essay)
    messages = [{"role": "user", "content": prompt}]
    try:
        resp = create(client, beta=True, model=MODEL, max_tokens=16000,
                      betas=[FETCH_BETA], tools=REVIEW_TOOLS, messages=messages)
    except Exception as exc:  # the beta refused, or the tool is gone
        print(f"web_fetch unavailable ({str(exc)[:120]}); reviewing with search only")
        resp = create(client, model=MODEL, max_tokens=16000,
                      tools=REVIEW_TOOLS[:1], messages=messages)
    for attempt in range(2):
        try:
            report = agent.extract_json(agent.text_blocks(resp), require=("verdict", "findings"))
            break
        except ValueError:
            if attempt == 1:
                raise
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                "That reply contained no JSON object. Reply with the JSON "
                "report described above and nothing else."})
            resp = create(client, model=MODEL, max_tokens=16000, messages=messages)
    report["findings"] = [f for f in report.get("findings", []) if isinstance(f, dict)]
    return report


def serious(report: dict) -> list:
    return [f for f in report["findings"] if f.get("severity") in ("error", "unsupported")]


def yaml_str(s) -> str:
    return json.dumps(str(s), ensure_ascii=False)


def front_matter(essay: dict, date: str, review: dict, passes: list) -> str:
    words = len(plain_body(essay["body"]).split())
    minutes = max(5, round(words / 230))
    tags = [t for t in essay.get("tags", []) if isinstance(t, str)][:4] or ["minds"]
    lines = [
        "---",
        f"title: {yaml_str(essay['title'])}",
        f"search_title: {yaml_str(essay.get('search_title') or essay['title'])}",
        f"description: {yaml_str(essay.get('description', ''))}",
        f"standfirst: {yaml_str(essay.get('standfirst', ''))}",
        f'reading_time: "about {minutes} minutes"',
        "tags: [" + ", ".join(tags) + "]",
        "layout: history.njk",
        f"date: {date}",
        'provenance: "agent"',
        "review:",
        f"  by: {yaml_str(REVIEW_BY + ' ' + passes_sentence(passes))}",
        f"  verdict: {yaml_str((str(review.get('verdict', '')) + '. ' + str(review.get('summary', ''))).strip())}",
        "  findings:",
    ]
    shown = [f for f in review["findings"] if f.get("severity") != "confirmed"]
    if not shown:
        lines[-1] = "  findings: []"
    for f in shown:
        lines.append(f"    - claim: {yaml_str(f.get('claim', ''))}")
        lines.append(f"      finding: {yaml_str(f.get('finding', ''))}")
        lines.append(f"      action: {yaml_str(f.get('action', ''))}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def passes_sentence(passes: list) -> str:
    parts = []
    for i, p in enumerate(passes, 1):
        n = len(serious(p))
        parts.append(f"Pass {i}: {n} error{'s' if n != 1 else ''} or unsupported claim{'s' if n != 1 else ''}"
                     + (", corrected" if n and i < len(passes) else "") + ".")
    return " ".join(parts) + " The last report is below, unedited."


# ------------------------------------------------------------------- main

def main() -> int:
    HIST.mkdir(parents=True, exist_ok=True)
    already = published_this_week()
    if already and not DRAFT:
        print(f"An essay went out this week ({already.name}). Standing down.")
        agent.set_output(held=True)
        return 0

    subject, done = next_subject()
    print(f"Subject: {subject}")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    brief = BRIEF.read_text(encoding="utf-8")
    date = today().strftime("%Y-%m-%d")

    messages = [{"role": "user", "content":
        brief
        + "\n\n## Already published (do not repeat)\n"
        + "\n".join(f"- {d}" for d in done)
        + f"\n\n## This week's subject\n\n{subject}\n\n"
        "Search first, widely, for primary sources and the scholarly record. "
        "Then write. Reply with the JSON object and nothing else."}]

    essay = None
    failures = []
    for attempt in range(3):
        resp = create(client, model=MODEL, max_tokens=MAX_TOKENS,
                      tools=WRITER_TOOLS, messages=messages)
        try:
            essay = agent.extract_json(agent.text_blocks(resp))
        except ValueError as exc:
            print(f"Attempt {attempt + 1} returned no usable JSON: {exc.args[0][:120]}")
            if attempt == 2:
                raise
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content":
                "That reply contained no JSON object. Do not narrate and do not "
                "search again. Reply with the JSON object described in the "
                "brief and nothing else, complete and valid."})
            continue
        failures = check_essay(essay["body"])
        if not failures:
            break
        print(f"Attempt {attempt + 1} failed local checks:\n  " + "\n  ".join(failures))
        if attempt == 2:
            break
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
            "The essay failed these checks:\n- " + "\n- ".join(failures)
            + "\n\nFix them and reply with the complete JSON object again, "
            "nothing else. Do not search again unless a footnote needs a page "
            "you have not found."})
    if essay is None:
        raise SystemExit("No essay.")
    if failures:
        return hold(essay, date, subject, "Failed local checks after three attempts:\n" + "\n".join(failures))

    # Peer review, up to REVIEW_PASSES times. The reviewer never sees the
    # drafts or the corrections, only the current essay.
    passes = []
    report = None
    for n in range(REVIEW_PASSES):
        report = run_review(client, essay)
        passes.append(report)
        bad = serious(report)
        print(f"Review pass {n + 1}: {report.get('verdict')}; {len(bad)} serious finding(s)")
        if not bad or n == REVIEW_PASSES - 1:
            break
        findings = "\n".join(
            f"- CLAIM: {f.get('claim')}\n  FINDING: {f.get('finding')}\n  ACTION: {f.get('action')}"
            for f in report["findings"] if f.get("severity") != "confirmed")
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content":
            "A reviewer opened every source and checked every quotation and "
            "claim. These are its findings. Correct every error and every "
            "unsupported claim: quote exactly or paraphrase without quotation "
            "marks, cut invented colour, mark interpretation as the essay's, "
            "fix or replace bad footnotes. Quibbles are worth fixing too. Then "
            "run your eye over the whole essay for anything of the same kind "
            "the reviewer did not list. Reply with the complete corrected JSON "
            "object, nothing else.\n\n" + findings})
        resp = create(client, model=MODEL, max_tokens=MAX_TOKENS,
                      tools=WRITER_TOOLS, messages=messages)
        try:
            essay = agent.extract_json(agent.text_blocks(resp))
        except ValueError as exc:
            return hold(essay, date, subject, f"Correction pass returned no JSON: {exc.args[0][:200]}")
        failures = check_essay(essay["body"])
        if failures:
            return hold(essay, date, subject, "Corrected essay failed local checks:\n" + "\n".join(failures))

    if serious(report) or str(report.get("verdict", "")).upper().startswith("DO NOT"):
        return hold(essay, date, subject,
                    "Errors survived the last review pass:\n"
                    + json.dumps(serious(report), indent=2, ensure_ascii=False))

    slug = agent.slugify(essay.get("search_title") or essay["title"])[:60].rstrip("-")
    filename = f"{date}-{slug}.md"
    text = front_matter(essay, date, report, passes) + essay["body"].strip() + "\n"
    if DRAFT:
        HELD.mkdir(exist_ok=True)
        (HELD / filename).write_text(text, encoding="utf-8")
        print(f"Draft written to agent/held/{filename}")
        agent.set_output(held=True)
        return 0
    (HIST / filename).write_text(text, encoding="utf-8")
    mark_done(subject, filename)
    LATEST.write_text(json.dumps({
        "title": essay["title"],
        "short_version": (essay.get("standfirst") or essay.get("description", ""))[:280],
        "url": f"{SITE}/history/{date}-{slug}/",
    }, indent=2), encoding="utf-8")
    agent.set_output(held=False)
    print(f"Published src/history/{filename}")
    return 0


def hold(essay: dict, date: str, subject: str, why: str) -> int:
    HELD.mkdir(exist_ok=True)
    path = HELD / f"history-{date}.md"
    path.write_text(f"# HELD: {subject}\n\n{why}\n\n---\n\n"
                    + json.dumps(essay, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"HELD: {why[:400]}")
    agent.set_output(held=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
