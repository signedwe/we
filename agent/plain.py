"""Plain-English checks for WE.

The brief says talk like a person. This file is what makes that a rule the
writer cannot skip. It measures four things a reader feels and cannot name:
how long the sentences run, how many words are the kind that only appear in
seminars, how much of the page is abstract nouns, and whether a person could
read it aloud without stopping. Thresholds were set on 17 September 2026 by
measuring the pages the operator called boring against the rewrites he
accepted; the boring ones fail, the rewrites pass.

Used two ways: check_post() calls check_plain() on the body of every
autonomous post, so the writer rewrites until it passes; and
_claude-publish/style.py runs it over a whole page for the conversation route.
"""
import re

# Word the writer reached for -> what a person would say. Quoted spans are
# skipped, so a source's own jargon can be quoted back at it.
JARGON = {
    "bloc": "a group that acts together, or name them",
    "asset lock": "a lock so nobody can sell the members out",
    "collecting society": "the body that collects the money",
    "governance": "who decides",
    "capacity": "what it can do",
    "coordination": "getting people to act together",
    "coordinate": "get people to act together",
    "accountability": "who answers for it",
    "accountable": "answers for it",
    "stakeholder": "say who",
    "stakeholders": "say who",
    "infrastructure": "say what: the wires, the servers, the roads",
    "optimise": "tune, or make better",
    "incentive": "reason, or what's in it for them",
    "incentives": "reasons",
    "dynamic": "cut it",
    "narrative": "story",
    "utilise": "use",
    "facilitate": "help, or let",
    "leverage": "a lever, or use",
    "operationalise": "do it",
    "interoperability": "works with the others",
    "remuneration": "pay",
    "counterparty": "the other side",
    "proposition": "idea, or claim",
    "instrument": "tool, or say which one",
    "configuration": "settings",
    "framework": "say what it is, or cut it",
    "structural": "cut it",
    "epistemic": "cut it",
    "mechanism": "how it works, or the lever",
    "ecosystem": "cut it",
    "paradigm": "cut it",
    "discourse": "cut it",
    "transformative": "cut it",
    "holistic": "cut it",
    "robust": "strong, or cut it",
    "synergy": "cut it",
    "scalable": "can grow",
    "granular": "detailed",
    "actionable": "cut it",
    "empower": "let",
    "empowers": "lets",
    "modality": "cut it",
    "normative": "about what should be",
    "heterogeneous": "mixed",
    "aggregation": "the bit that adds it up",
    "jurisdiction": "where, or whose law",
    "in terms of": "cut it",
    "with respect to": "about",
    "in the context of": "in, or cut it",
    "it is worth noting": "cut it",
    "it should be noted": "cut it",
    "arguably": "cut it, and decide",
}

# Words WE has to use sometimes because they are the subject. Printed on the
# scorecard so the writer looks twice; they never fail a page on their own.
WATCH = {
    "mutual": "fine when it is the legal form; otherwise club, society, or say what it is",
    "subordinate": "under, or obeys, unless quoting the code",
    "portability": "taking it with you, unless it is the legal term",
    "institution": "name the actual body if you can",
    "institutions": "name the actual bodies if you can",
    "incumbent": "the one already there",
}

# Machine tells. Words and moves that appear in machine-written prose far
# more than in anything a person would say to a friend. Fail on sight.
AIISMS = (
    "delve", "delves", "delving", "tapestry", "navigate", "navigating",
    "landscape", "unpack", "underscore", "underscores", "testament to",
    "foster", "fosters", "fostering", "resonate", "resonates", "nuanced",
    "multifaceted", "pivotal", "game-changer", "game changer", "seamless",
    "seamlessly", "vibrant", "realm", "beacon", "journey", "elevate",
    "harness", "unlock", "unlocks", "supercharge", "dive into", "deep dive",
    "crucial", "crucially", "ultimately", "notably", "importantly",
    "here's the thing", "here is the thing", "let's be clear", "let's be honest",
    "make no mistake", "in a world where", "at the end of the day",
    "the reality is", "simply put", "put simply", "to be clear",
    "let that sink in", "read that again", "the takeaway", "key takeaway",
    "food for thought", "a lot to unpack", "moving forward", "going forward",
    "double down", "it's worth noting", "worth noting", "it bears repeating",
    "in today's", "in an era", "in the age of", "as we move", "the bottom line",
    "rich history", "stark reminder", "sobering", "chilling", "profound",
    "paradigm shift", "sea change", "watershed", "existential",
    "not just", "isn't just", "is not just", "more than just", "not only",
    "boasts", "showcases", "spearhead", "myriad", "plethora", "utilize",
    "additionally", "furthermore", "moreover", "in conclusion", "overall,",
    "that said,", "having said that", "with that said", "needless to say",
    "arguably", "it goes without saying", "ever-evolving", "ever-changing",
    "cutting-edge", "state-of-the-art", "groundbreaking", "revolutionary",
    "transformative", "innovative", "empower", "empowers", "empowering",
    "the question is", "the real question", "the question isn't",
    "spoiler:", "plot twist", "hot take", "unpopular opinion",
)

# The contrast move: "It isn't X. It's Y." Once a page, it lands. Three times,
# the reader hears the machine.
CONTRAST = re.compile(
    r"\b(?:isn't|is not|wasn't|aren't|not)\b[^.!?\n]{1,60}[.!?]\s+"
    r"(?:It's|It is|That's|That is|They're|It was)\b", re.I)
CONTRAST_MAX = 2          # per body
CONTRAST_MAX_SHORT = 1    # per voice or proposal

# Short spans (a voice, a proposal) get the same jargon rule and a looser
# version of the numbers: nobody can fit a five-word sentence and a spread
# of lengths into eighty words without it sounding forced.
SHORT_SPAN = 150         # words; below this the loose numbers apply
TINY_SPAN = 20           # words; below this only the jargon rule applies
SHORT_FLESCH_FLOOR = 65
SHORT_AVG_SENTENCE_MAX = 16
SHORT_ABSTRACT_PER_100_MAX = 4.0

# Lower-case only, so the OpenAI Foundation and the DeepMind Institute are
# names, not abstractions.
ABSTRACT = re.compile(r"\b[a-z]+(?:tion|sion|ity|ness|ment|ance|ence|ism)s?\b")
# Look abstract, aren't: things you can point at.
CONCRETE = {
    "sentence", "sentences", "licence", "licences", "section", "sections",
    "question", "questions", "comment", "comments", "document", "documents",
    "mention", "mentions", "business", "businesses", "moment", "moments",
    "payment", "payments", "station", "stations", "nation", "nations",
    "science", "evidence", "audience", "distance", "silence", "patience",
    "witness", "witnesses", "apartment", "basement", "pavement", "cement",
    "election", "elections", "pension", "pensions", "mission", "missions",
    "version", "versions", "edition", "editions", "fence", "fences",
    "city", "cities", "charity", "charities", "university", "universities",
    "tenement", "parliament", "equipment", "instrument", "instruments",
}

# Thresholds. A reader feels every one of these.
FLESCH_FLOOR = 70        # reading ease; 70 is a person talking, 55 is a report
AVG_SENTENCE_MAX = 15    # words
LONGEST_SENTENCE_MAX = 40
LONG_SHARE_MAX = 15      # per cent of sentences over 25 words
ABSTRACT_PER_100_MAX = 3.0
UNDER_FIVE_MIN = 1       # sentences under five words


def _strip_links(text: str) -> str:
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text or "")


def _strip_quotes(text: str) -> str:
    text = re.sub(r"[“”]", '"', text)
    return re.sub(r'"[^"\n]{1,300}"', " ", text)


def sentences(text: str) -> list:
    text = _strip_links(text)
    text = re.sub(r"\s+", " ", text)
    # A full stop inside a closing quote still ends the sentence.
    return [s.strip() for s in re.split(r"(?<=[.!?])[\"”’']*\s+", text.strip()) if s.strip()]


def _syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    # Silent endings: -e (make), -es after most consonants (makes, reserves),
    # -ed unless it follows t or d (walked, but wanted).
    if n > 1:
        if w.endswith("e") and not w.endswith("le"):
            n -= 1
        elif w.endswith("es") and not re.search(r"(?:[sxz]|ch|sh|[^aeiou]l)es$", w):
            n -= 1
        elif w.endswith("ed") and not w.endswith(("ted", "ded")):
            n -= 1
    return max(1, n)


def metrics(text: str) -> dict:
    sents = sentences(text)
    words = [w for s in sents for w in re.findall(r"[A-Za-z']+", s)]
    if not words or not sents:
        return {}
    # Reading ease is scored on the writer's own words: what a source said is
    # quoted, not written, and a page is not marked down for quoting it.
    unquoted = _strip_quotes(_strip_links(text))
    own_sents = sentences(unquoted) or sents
    own_words = [w for s in own_sents for w in re.findall(r"[A-Za-z']+", s)] or words
    syl = sum(_syllables(w) for w in own_words)
    abstract = [w for w in ABSTRACT.findall(unquoted) if w.lower() not in CONCRETE]
    lens = [len(re.findall(r"[A-Za-z']+", s)) for s in sents]
    watch = []
    for term in WATCH:
        n = len(re.findall(r"\b" + re.escape(term) + r"\b", unquoted, re.I))
        if n:
            watch.append((term, n))
    aiisms = []
    for term in AIISMS:
        n = len(re.findall(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", unquoted, re.I))
        if n:
            aiisms.append((term, n))
    contrasts = len(CONTRAST.findall(unquoted))
    jargon = []
    for term in JARGON:
        n = len(re.findall(r"\b" + re.escape(term) + r"\b", unquoted, re.I))
        if n:
            jargon.append((term, n))
    return {
        "words": len(words),
        "sentences": len(sents),
        "avg_sentence": round(sum(lens) / len(lens), 1),
        "longest": max(lens),
        "long_share": round(100 * sum(l > 25 for l in lens) / len(lens)),
        "under_five": sum(l < 5 for l in lens),
        "flesch": round(206.835 - 1.015 * (len(own_words) / len(own_sents)) - 84.6 * (syl / len(own_words))),
        "abstract_per_100": round(100 * len(abstract) / len(words), 1),
        "jargon": jargon,
        "watch": watch,
        "aiisms": aiisms,
        "contrasts": contrasts,
    }


def check_plain(text: str) -> list:
    """Every way the text fails to sound like a person. Empty means it passes.

    A body gets the full numbers. A span under SHORT_SPAN words (a voice, a
    proposal) gets the loose ones. A span under TINY_SPAN words is only
    checked for seminar words: you cannot measure the rhythm of one line.
    """
    m = metrics(text)
    if not m:
        return []
    out = []
    if m["jargon"]:
        items = "; ".join(f'"{t}" ({n}) -> {JARGON[t]}' for t, n in m["jargon"])
        out.append(
            f"Seminar words: {items}. A word that shows up more in seminars "
            "than in kitchens is doing the opposite of what you think. Say the "
            "plain thing, or name the actual body, person or object."
        )
    if m["aiisms"]:
        items = ", ".join(f'"{t}"' + (f" x{n}" if n > 1 else "") for t, n in m["aiisms"])
        out.append(
            f"Machine tells: {items}. Nobody says these to a friend; a model "
            "says them to everyone. Cut the word or say the plain thing. If "
            "the sentence dies without it, the sentence had nothing in it."
        )
    if m["words"] < TINY_SPAN:
        return out
    short = m["words"] < SHORT_SPAN
    cmax = CONTRAST_MAX_SHORT if short else CONTRAST_MAX
    if m["contrasts"] > cmax:
        out.append(
            f"The contrast move ('It isn't X. It's Y.') {m['contrasts']} times; "
            f"the most is {cmax}. Once it lands. Repeated, it is a tic the "
            "reader can hear. Say the Y and drop the X."
        )
    flesch_floor = SHORT_FLESCH_FLOOR if short else FLESCH_FLOOR
    avg_max = SHORT_AVG_SENTENCE_MAX if short else AVG_SENTENCE_MAX
    abstract_max = SHORT_ABSTRACT_PER_100_MAX if short else ABSTRACT_PER_100_MAX
    if m["flesch"] < flesch_floor:
        out.append(
            f"Reads like a report: reading ease {m['flesch']}, the floor is "
            f"{flesch_floor}. Shorter words, shorter sentences. If you could "
            "not say it in a pub without someone asking what a word means, "
            "rewrite it."
        )
    if m["avg_sentence"] > avg_max:
        out.append(
            f"Sentences average {m['avg_sentence']} words; the ceiling is "
            f"{avg_max}. Full stops cost nothing."
        )
    if m["longest"] > LONGEST_SENTENCE_MAX:
        out.append(
            f"One sentence runs to {m['longest']} words. Nothing over "
            f"{LONGEST_SENTENCE_MAX}. Cut it in two, or three."
        )
    if m["abstract_per_100"] > abstract_max:
        out.append(
            f"{m['abstract_per_100']} abstract nouns per hundred words "
            f"(-tion, -ity, -ness, -ment); the ceiling is {abstract_max}. "
            "If a sentence has no object anybody could photograph, it is a "
            "sentence about nothing. Put a person, a thing or a number in it."
        )
    if not short:
        if m["long_share"] > LONG_SHARE_MAX:
            out.append(
                f"{m['long_share']} per cent of sentences run past 25 words; the "
                f"ceiling is {LONG_SHARE_MAX}. That is a hedge trimmed flat."
            )
        if m["under_five"] < UNDER_FIVE_MIN:
            out.append("Nothing short anywhere. At least one sentence under five words. Short. Like that.")
    return out


def scorecard(text: str) -> str:
    m = metrics(text)
    if not m:
        return "nothing to measure"
    short = m["words"] < SHORT_SPAN
    fl = SHORT_FLESCH_FLOOR if short else FLESCH_FLOOR
    av = SHORT_AVG_SENTENCE_MAX if short else AVG_SENTENCE_MAX
    ab = SHORT_ABSTRACT_PER_100_MAX if short else ABSTRACT_PER_100_MAX
    jar = ", ".join(f"{t} x{n}" for t, n in m["jargon"]) or "none"
    watch = ", ".join(f"{t} x{n}" for t, n in m["watch"])
    watch = f" | watch: {watch}" if watch else ""
    ai = ", ".join(f"{t} x{n}" for t, n in m["aiisms"])
    ai = f" | machine tells: {ai}" if ai else ""
    return (
        f"words {m['words']} | sentences {m['sentences']} | avg {m['avg_sentence']} "
        f"(max {av}) | longest {m['longest']} (max {LONGEST_SENTENCE_MAX}) | "
        f"over-25 {m['long_share']}% | under-5 {m['under_five']} | "
        f"reading ease {m['flesch']} (min {fl}) | abstract/100 {m['abstract_per_100']} "
        f"(max {ab}) | contrast moves {m['contrasts']} | seminar words: {jar}{watch}{ai}"
    )
