"""Pictures for WE, made by an image model and chosen by a second machine.

    WE_ART=1 python scripts/art.py --post src/posts/2026-11-25-some-post.md
    WE_ART=1 python scripts/art.py --latest          # the post in agent/latest.json

Off unless WE_ART=1. With the flag off, a key missing, the day's budget
spent, or the image service failing, this prints why and exits 0: the post
keeps its text-led layout and nothing else changes. A picture is never a
reason for a post not to go out.

What it does, for one post:

  1. A language model reads the piece and proposes three different pictures,
     each with its own argument, then picks one (two for a heresy).
  2. The image service draws them. At most two to begin with, and one retry.
  3. The language model looks at the actual pictures, not the prompts, and
     chooses one, asks for one more try, or says none is good enough.
  4. The winner is saved as WebP in src/static/art/, with a social-card crop
     and a thumbnail, alt text and a visible "made by a machine" credit.
  5. The post's front matter gets an `artwork:` block, agent/art.json gets
     an entry for the gallery, and agent/art-ledger.json records what was
     asked for and what the service says it used.

The image service is behind one function per provider, so another can be
added without touching the rest. Settings, all optional:

  WE_ART_PROVIDER      openai (default) | test (draws a placeholder, no network)
  WE_ART_MODEL         image model name; if unset, the list in MODELS is tried in order
  WE_ART_SIZE          default 1536x1024
  WE_ART_QUALITY       default medium
  WE_ART_DAILY_USD     stop before the day's estimated spend passes this (default 3.00)
  WE_ART_EST_USD       the estimate charged per picture against that budget (default 0.25,
                       set high on purpose; the ledger also keeps the service's own usage)
  WE_ART_DAILY_IMAGES  hard cap on pictures per day (default 8)
  WE_ART_FORMS         which kinds of post get a picture (default heresy,satire,five_years,obituary)
  WE_ART_DIRECTOR      language model for steps 1 and 3 (default claude-sonnet-5-5)

Keys come from the environment only (OPENAI_API_KEY, ANTHROPIC_API_KEY).
They are never written to a file, a log or the page.
"""
import argparse
import base64
import io
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "static" / "art"
MANIFEST = ROOT / "agent" / "art.json"
LEDGER = ROOT / "agent" / "art-ledger.json"
LATEST = ROOT / "agent" / "latest.json"
# A pilot draws the pictures but hangs nothing: files go to pilot/art/, which
# the site does not build, and the post is left alone. --promote hangs them.
PILOT = ROOT / "pilot"
PILOT_OUT = PILOT / "art"
PILOT_MANIFEST = PILOT / "art.json"
# Pictures whose idea and instruction were written in conversation, not by
# the director model: {slug: {title, form, post, idea, tradition, prompt, alt}}.
COMMISSIONS = PILOT / "commissions.json"

# The switch and the caps. agent/art-config.json is the standing setting;
# an environment variable, where set, wins for that run.
CONFIG = {}
try:
    CONFIG = json.loads((ROOT / "agent" / "art-config.json").read_text(encoding="utf-8"))
except Exception:
    pass


def setting(env: str, key: str, default):
    return os.environ.get(env) or CONFIG.get(key) or default


ON = os.environ.get("WE_ART") == "1" or (os.environ.get("WE_ART") != "0" and CONFIG.get("on") is True)
PROVIDER = os.environ.get("WE_ART_PROVIDER", "openai")
# Tried in order until the service accepts one. Names move; set WE_ART_MODEL
# to pin one once the pilot shows which this account has.
MODELS = [m for m in [str(setting("WE_ART_MODEL", "model", "")).strip()] if m] or [
    "gpt-image-2.6-flare", "gpt-image-2.5-flare", "gpt-image-2", "gpt-image-1.5", "gpt-image-1"]
SIZE = os.environ.get("WE_ART_SIZE", "1536x1024")
QUALITY = os.environ.get("WE_ART_QUALITY", "medium")
DAILY_USD = float(setting("WE_ART_DAILY_USD", "daily_usd", "3.00"))
EST_USD = float(setting("WE_ART_EST_USD", "est_usd", "0.25"))
DAILY_IMAGES = int(setting("WE_ART_DAILY_IMAGES", "daily_images", "8"))
MONTHLY_IMAGES = int(setting("WE_ART_MONTHLY_IMAGES", "monthly_images", "60"))
FORMS = [f.strip() for f in os.environ.get("WE_ART_FORMS", "heresy,satire,five_years,obituary").split(",")]
DIRECTOR = os.environ.get("WE_ART_DIRECTOR", "claude-sonnet-5-5")
DIRECTOR_FALLBACK = "claude-sonnet-4-6"
FIRST_ROUND_MAX = 2
RETRIES = 1

VISUAL = """You are the art director of WE, a site about what a world with AI could be. You do not draw. You decide what the picture is, and an image model draws it.

The picture is not an illustration of the article. It makes a statement of its own: it can push the argument further, contradict it, mock it, or show its most extreme result.

Ask for things that could not exist, could not be photographed, and would cost a fortune to stage. Borrow from anywhere: surrealism, Dada, political caricature, Renaissance painting, absurd photography, medieval manuscripts, propaganda posters, Victorian engraving, collage, natural-history dioramas, altarpieces, tapestries, banknotes, museum cases. Mix periods, scales and materials. Invent impossible objects, ridiculous institutions, strange rituals, odd versions of ordinary life. Beautiful, grotesque, funny, unsettling or absurd are all fine. Tasteful is not required.

Go further than feels safe. The operator, 25 November 2026, on the first three pictures: "they're not bad, they should be even crazier". Those three were each a handsome copy of one old style with one tidy metaphor in the middle. That is the failure to avoid.

- Change the medium every time. Not another oil painting, engraving, manuscript or museum case: the first pictures were all handsome copies of something made before 1900. Reach for flash photography of an impossible scene, claymation, cut-paper collage, a propaganda poster, a 1970s mail-order catalogue page, a children's-book spread, a cutaway technical drawing, a seaside postcard, a CCTV still of something absurd, embroidery, a board-game box.
- Collide things. Two worlds that have no business in one frame: an altarpiece with a self-checkout in it, a royal procession through a call centre, a whale beached in a spreadsheet. One style on its own, done well, is a pastiche and is not enough.
- Something is happening, and it is going wrong. A moment, not a display. Somebody is falling, fleeing, eating, signing, auctioning, drowning in something.
- Break scale. A banker the size of a cathedral. A parliament in a teacup.
- Put jokes in the corners. A second and third thing to find after the first.
- It should make a stranger laugh or wince before they understand it. If it would hang quietly in a nice hotel, start again.
- For each idea, write it, then ask what the braver version is, and use that one.
- One of your three must be the picture you would be nervous to show. Choose it unless it breaks a hard limit.

Never: glowing brains, humanoid robots, blue circuitry, holograms, people staring at screens, handshakes between a human and a machine, a lightbulb, a chess piece.

Hard limits.
- No real, recognisable person, living or dead. No real company's logo or product. No copy of an existing artwork or a named living artist's style.
- Nothing that could pass for a news photograph or a historical document of a real event. If it looks photographic, it must be plainly impossible.
- No words in the picture unless the idea needs a few (a placard, a banknote), and then give the exact words, in capitals, and say "no other text". Never the name of a real company, brand, bank, party or newspaper, on anything, however small.
- Nothing hateful, sexual or gory. Nobody identifiable from the article.
- Never put any detail about who runs this site, or any private detail, into a prompt."""


def say(msg: str) -> None:
    print(f"art: {msg}")


def stop(msg: str) -> int:
    say(msg + " The post keeps its text-led layout.")
    return 0


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save(path, data) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def spent_today(ledger: list) -> tuple:
    rows = [r for r in ledger if r.get("date") == today()]
    return sum(float(r.get("est_usd") or 0) for r in rows), sum(int(r.get("images") or 0) for r in rows)


def allowance(ledger: list) -> int:
    """How many more pictures today's budget allows."""
    usd, n = spent_today(ledger)
    by_money = int((DAILY_USD - usd + 1e-9) // EST_USD) if EST_USD > 0 else DAILY_IMAGES
    month = sum(int(r.get("images") or 0) for r in ledger if str(r.get("date", "")).startswith(today()[:7]))
    return max(0, min(by_money, DAILY_IMAGES - n, MONTHLY_IMAGES - month))


# ----------------------------------------------------------------------
# the image services
# ----------------------------------------------------------------------

class ModelRefused(Exception):
    pass


def openai_generate(prompt: str, model: str) -> tuple:
    """One picture. Returns (png bytes, usage dict)."""
    key = os.environ["OPENAI_API_KEY"]
    body = json.dumps({"model": model, "prompt": prompt, "n": 1, "size": SIZE,
                       "quality": QUALITY, "output_format": "png"}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body,
                                 headers={"Authorization": "Bearer " + key,
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:400]
        try:
            err = json.loads(detail).get("error", {})
            detail = f"{err.get('code') or err.get('type')}: {err.get('message')}"
        except Exception:
            pass
        if exc.code in (400, 403, 404) and re.search(r"model|not found|does not exist|access|verif|unsupported|invalid.*(size|quality)",
                                                      detail, re.I):
            raise ModelRefused(f"{model}: {detail[:240]}")
        raise RuntimeError(f"image service said {exc.code}: {detail[:240]}")
    b64 = (data.get("data") or [{}])[0].get("b64_json")
    if not b64:
        raise RuntimeError("image service returned no picture")
    return base64.b64decode(b64), data.get("usage") or {}


def test_generate(prompt: str, model: str) -> tuple:
    """A placeholder drawn locally, for testing the pipe with no network."""
    from PIL import Image, ImageDraw
    w, h = (int(x) for x in SIZE.split("x"))
    img = Image.new("RGB", (w, h), (204, 75, 31))
    d = ImageDraw.Draw(img)
    for i in range(0, w, 64):
        d.line([(i, 0), (w - i, h)], fill=(0, 0, 0), width=3)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue(), {"test": True}


PROVIDERS = {"openai": openai_generate, "test": test_generate}


def generate(prompt: str, state: dict) -> tuple:
    fn = PROVIDERS[PROVIDER]
    if PROVIDER == "test":
        state["model"] = "test"
        return fn(prompt, "test")
    for model in ([state["model"]] if state.get("model") else MODELS):
        try:
            png, usage = fn(prompt, model)
            state["model"] = model
            return png, usage
        except ModelRefused as exc:
            say(f"not available, trying the next model. {exc}")
    raise RuntimeError("no image model on the list was accepted; set WE_ART_MODEL")


# ----------------------------------------------------------------------
# the art director
# ----------------------------------------------------------------------

def director(messages: list, max_tokens: int = 2500) -> str:
    return json.dumps(director_json(messages, max_tokens))


CONCEPT_SCHEMA = {"type": "object", "required": ["concepts", "chosen"], "properties": {
    "concepts": {"type": "array", "items": {"type": "object", "required": ["idea", "tradition", "prompt", "alt"],
                 "properties": {"idea": {"type": "string"}, "tradition": {"type": "string"},
                                "prompt": {"type": "string"}, "alt": {"type": "string"}}}},
    "chosen": {"type": "array", "items": {"type": "integer"}}}}
JUDGE_SCHEMA = {"type": "object", "required": ["pick", "why"], "properties": {
    "pick": {"type": "integer"}, "why": {"type": "string"}, "retry_prompt": {"type": "string"}}}


def director_json(messages: list, max_tokens: int = 2500, schema: dict = None) -> dict:
    """Ask the art director. The answer comes back through a forced tool
    call, so it is always a well-formed object: twice on 25 November a
    reply written as plain JSON would not parse and the picture was lost."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    tool = {"name": "answer", "description": "Give your answer.", "input_schema": schema or {"type": "object"}}
    last = None
    for model in dict.fromkeys([DIRECTOR, DIRECTOR_FALLBACK]):
        try:
            resp = client.messages.create(model=model, max_tokens=max_tokens, messages=messages,
                                          tools=[tool], tool_choice={"type": "tool", "name": "answer"})
            for block in resp.content:
                if getattr(block, "type", "") == "tool_use":
                    return dict(block.input)
            raise RuntimeError("the art director gave no answer")
        except Exception as exc:
            last = exc
            if type(exc).__name__ not in ("NotFoundError", "BadRequestError", "PermissionDeniedError"):
                raise
    raise last


def as_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])


def recent_traditions(n: int = 8) -> list:
    rows = load(MANIFEST, []) + load(PILOT_MANIFEST, [])
    return [str(r.get("tradition")) for r in rows[-n:] if r.get("tradition")]


def concepts(title: str, form: str, body: str, want: int) -> dict:
    if os.environ.get("WE_ART_DIRECTOR") == "stub":
        return {"concepts": [{"idea": "A test card.", "tradition": "test", "prompt": "a test card", "alt": "A test card."}],
                "chosen": [1]}
    prompt = f"""{VISUAL}

---

The piece ({form}): {title}

{body[:9000]}

Propose three pictures that are really different from each other: different idea, different tradition, different joke. The last pictures on this site borrowed from: {"; ".join(recent_traditions()) or "nothing yet"}. Use none of those traditions again, and nothing close to them: the site must not settle into one look. Then choose the {'two strongest' if want > 1 else 'strongest'}.

Answer with the tool, in this shape:

{{"concepts": [{{"idea": "what the picture argues, in one plain sentence a reader could be shown under it. never the word room, never an em dash",
               "tradition": "the visual tradition it borrows",
               "prompt": "the full instruction for the image model: subject, composition, medium, period, lighting, palette, what is in the foreground and background. 80 to 160 words. Landscape format.",
               "alt": "alt text: what is in the picture, plainly, for someone who cannot see it. One sentence."}}],
  "chosen": [the numbers of the chosen concepts, counting from 1]}}"""
    return director_json([{"role": "user", "content": prompt}], max_tokens=5000, schema=CONCEPT_SCHEMA)


def judge(title: str, shots: list) -> dict:
    """Look at the pictures themselves. shots: [{idea, prompt, png}]."""
    if os.environ.get("WE_ART_DIRECTOR") == "stub":
        return {"pick": 1, "why": "stub"}
    from PIL import Image
    content = [{"type": "text", "text": f"""{VISUAL}

---

These pictures were made for the piece "{title}". Judge what is actually in them, not what was asked for.

Pick the strangest one that works: the one a stranger would stop on and send to a friend. Wit and nerve first, then composition, then whether the details that matter came out. A handsome, calm picture loses to an odd one. Read every piece of lettering in each picture, however small: trophies, labels, signs, spines. Refuse any picture in which you can read the name of a real company, brand, bank, party or newspaper (the first pilot let one through on a trophy). Refuse any picture that: shows a recognisable real person or logo; could be mistaken for a photograph or document of a real event; has garbled or wrong lettering that a reader would notice; has mangled hands or faces that spoil it; or falls back on a cliché from the never-list.

Answer with the tool, in this shape:

{{"pick": the number of the best usable picture counting from 1, or 0 if none is usable,
  "why": "one sentence",
  "retry_prompt": "if pick is 0, or the best is only fair, a rewritten prompt for one more try. empty if the pick is good"}}"""}]
    for i, s in enumerate(shots, 1):
        img = Image.open(io.BytesIO(s["png"])).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        content.append({"type": "text", "text": f"Picture {i}. The idea was: {s['idea']}"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                    "data": base64.b64encode(buf.getvalue()).decode()}})
    return director_json([{"role": "user", "content": content}], max_tokens=1500, schema=JUDGE_SCHEMA)


# ----------------------------------------------------------------------
# files
# ----------------------------------------------------------------------

def cover(img, w: int, h: int):
    """Crop to w x h from the centre, keeping as much as fits."""
    from PIL import Image
    scale = max(w / img.width, h / img.height)
    r = img.resize((max(w, round(img.width * scale)), max(h, round(img.height * scale))), Image.LANCZOS)
    x, y = (r.width - w) // 2, (r.height - h) // 2
    return r.crop((x, y, x + w, y + h))


def write_images(slug: str, png: bytes, OUT=OUT) -> dict:
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(png)).convert("RGB")
    if img.width > 1600:
        img = img.resize((1600, round(img.height * 1600 / img.width)), Image.LANCZOS)
    img.save(OUT / f"{slug}.webp", "WEBP", quality=82, method=6)
    cover(img, 1200, 630).save(OUT / f"{slug}-card.jpg", "JPEG", quality=85, optimize=True)
    cover(img, 600, 400).save(OUT / f"{slug}-thumb.webp", "WEBP", quality=78, method=6)
    for name in (f"{slug}.webp", f"{slug}-card.jpg", f"{slug}-thumb.webp"):
        if (OUT / name).stat().st_size < 2000:
            raise RuntimeError(f"{name} came out empty")
    return {"file": f"{slug}.webp", "card": f"{slug}-card.jpg", "thumb": f"{slug}-thumb.webp",
            "width": img.width, "height": img.height}


def split_post(text: str) -> tuple:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("no front matter")
    return m.group(1), m.group(2)


def field(front: str, key: str) -> str:
    m = re.search(rf'^{key}:\s*"?(.*?)"?\s*$', front, re.M)
    return m.group(1) if m else ""


def set_artwork(path: pathlib.Path, art: dict) -> None:
    front, body = split_post(path.read_text(encoding="utf-8"))
    front = re.sub(r"\nartwork:\n(?:  .*\n?)*", "\n", front + "\n").rstrip("\n")
    y = lambda s: json.dumps(str(s), ensure_ascii=False)
    block = "\n".join(["artwork:", f"  file: {y(art['file'])}", f"  card: {y(art['card'])}",
                       f"  thumb: {y(art['thumb'])}", f"  width: {art['width']}", f"  height: {art['height']}",
                       f"  alt: {y(art['alt'])}", f"  concept: {y(art['concept'])}", f"  model: {y(art['model'])}"])
    path.write_text(f"---\n{front}\n{block}\n---\n{body}", encoding="utf-8")


# ----------------------------------------------------------------------
# one post
# ----------------------------------------------------------------------

def make(path: pathlib.Path, force: bool = False, candidates: int = 0, pilot: bool = False,
         commission: dict = None) -> int:
    if not ON:
        return stop("switched off (agent/art-config.json).")
    if commission:
        # The idea was written in conversation. The post may not be up yet;
        # a commission is always a pilot, hung later with --promote.
        front, body, pilot, force = "", "", True, True
        form, title, slug = commission.get("form", ""), commission["title"], path.stem
    else:
        if not path.exists():
            return stop(f"no such post: {path}.")
        front, body = split_post(path.read_text(encoding="utf-8"))
        form = field(front, "form") or "response"
        title = field(front, "title")
        slug = path.stem
    if form not in FORMS and not force:
        return stop(f"a {form} post gets no picture (WE_ART_FORMS).")
    if "\nartwork:" in "\n" + front and not force:
        return stop("this post already has a picture.")
    if PROVIDER not in PROVIDERS:
        return stop(f"unknown provider {PROVIDER}.")
    if PROVIDER == "openai" and not os.environ.get("OPENAI_API_KEY"):
        return stop("no OPENAI_API_KEY in the environment.")
    if os.environ.get("WE_ART_DIRECTOR") != "stub" and not os.environ.get("ANTHROPIC_API_KEY"):
        return stop("no ANTHROPIC_API_KEY for the art director.")
    if commission:
        candidates = 1

    ledger = load(LEDGER, [])
    room = allowance(ledger)
    if room < 1:
        usd, n = spent_today(ledger)
        return stop(f"today's budget is spent ({n} pictures, about ${usd:.2f} of ${DAILY_USD:.2f}).")

    want = candidates or (2 if form == "heresy" else 1)
    want = max(1, min(want, FIRST_ROUND_MAX, room))
    state, shots, used = {}, [], []

    def draw(idea: dict) -> None:
        png, usage = generate(idea["prompt"], state)
        shots.append({"idea": idea["idea"], "prompt": idea["prompt"], "alt": idea.get("alt", ""),
                      "tradition": idea.get("tradition", ""), "png": png})
        used.append(usage)
        ledger.append({"date": today(), "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "post": slug, "provider": PROVIDER, "model": state.get("model"), "size": SIZE,
                       "quality": QUALITY, "images": 1, "est_usd": EST_USD, "usage": usage})
        save(LEDGER, ledger)

    try:
        plan = {"concepts": [commission], "chosen": [1]} if commission else concepts(title, form, body, want)
        ideas = [c for c in plan.get("concepts") or [] if isinstance(c, dict) and c.get("prompt")]
        order = [int(i) - 1 for i in (plan.get("chosen") or [1]) if str(i).isdigit() and 0 < int(i) <= len(ideas)]
        order = (order or [0])[:want]
        say(f"{len(ideas)} ideas for \"{title}\"; drawing {len(order)}.")
        for i in order:
            say(f"  idea: {ideas[i]['idea']}")
            draw(ideas[i])
        verdict = judge(title, shots)
        pick = int(verdict.get("pick") or 0)
        retry = str(verdict.get("retry_prompt") or "").strip()
        if retry and RETRIES and allowance(ledger) >= 1:
            say(f"one more try. {verdict.get('why')}")
            base = shots[pick - 1] if pick else shots[0]
            draw({"idea": base["idea"], "prompt": retry, "alt": base["alt"]})
            verdict = judge(title, shots)
            pick = int(verdict.get("pick") or 0)
        if pick < 1 or pick > len(shots):
            return stop(f"none of the {len(shots)} pictures was good enough. {verdict.get('why') or ''}")
        chosen = shots[pick - 1]
        files = write_images(slug, chosen["png"], PILOT_OUT if pilot else OUT)
    except Exception as exc:
        return stop(f"failed ({type(exc).__name__}: {str(exc)[:300]}).")

    art = dict(files, alt=chosen["alt"] or chosen["idea"], concept=chosen["idea"], model=state.get("model") or PROVIDER)
    date = field(front, "date")[:10] or today()
    standalone = bool(commission and commission.get("standalone"))
    entry = dict(art, slug=slug, title=title, post_url="" if standalone else f"/{'history' if path.parent.name == 'history' else 'posts'}/{slug}/", date=date,
                 standalone=standalone, caption=(commission or {}).get("caption", ""),
                 tradition=chosen.get("tradition", ""),
                 prompt=chosen["prompt"], considered=len(shots), provider=PROVIDER,
                 post=str(path.relative_to(ROOT)))
    target = PILOT_MANIFEST if pilot else MANIFEST
    if pilot:
        PILOT.mkdir(exist_ok=True)
    else:
        set_artwork(path, art)
    manifest = [m for m in load(target, []) if m.get("slug") != slug]
    manifest.append(entry)
    save(target, manifest)
    usd, n = spent_today(ledger)
    say(f"hung {files['file']} ({state.get('model')}, {len(shots)} drawn; today {n} pictures, about ${usd:.2f}). {verdict.get('why') or ''}")
    return 0


def gallery() -> int:
    """A picture for its own sake, with no article behind it: a fictional
    advert, a banknote from a country that does not exist, a museum piece, a
    visual joke. At most one every three days, inside the same caps."""
    if not ON:
        return stop("switched off (agent/art-config.json).")
    rows = load(MANIFEST, [])
    alone = [r for r in rows if r.get("standalone")]
    if alone and (datetime.now(timezone.utc).date() - datetime.fromisoformat(alone[-1]["date"]).date()).days < int(CONFIG.get("gallery_every_days", 3)):
        return 0
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("ANTHROPIC_API_KEY"):
        return stop("no keys for a gallery picture.")
    if allowance(load(LEDGER, [])) < 1:
        return stop("today's budget is spent.")
    recent = "; ".join(f"{r.get('title')} ({r.get('tradition')})" for r in rows[-10:]) or "nothing yet"
    prompt = f"""{VISUAL}

---

This one is for the gallery, Impossible Pictures, and belongs to no article. It has to stand alone and be worth sending to a friend with no explanation.

Kinds of thing the gallery wants: an advert from 2050; a banknote, stamp or passport from a country that does not exist; an exhibit from a museum of the future; a public information poster for a problem we do not have yet; a seaside postcard from somewhere impossible; a page from an instruction manual for being human; a class photograph of something that has no class; a visual joke with nothing to say.

Already hanging, so do none of these again and borrow none of their looks: {recent}.

Propose three, each a different kind and a different medium, then choose the one you would be nervous to show.

Answer with the tool, in this shape:

{{"concepts": [{{"title": "the title on the gallery wall, a few words",
               "idea": "one plain sentence for the caption",
               "tradition": "the medium and look",
               "prompt": "the full instruction for the image model, 80 to 160 words, landscape. Give any lettering exactly, in capitals, and say no other text",
               "alt": "what is in the picture, plainly, for someone who cannot see it"}}],
  "chosen": [the number of the chosen one]}}"""
    schema = json.loads(json.dumps(CONCEPT_SCHEMA))
    schema["properties"]["concepts"]["items"]["properties"]["title"] = {"type": "string"}
    try:
        plan = director_json([{"role": "user", "content": prompt}], max_tokens=5000, schema=schema)
        ideas = [c for c in plan.get("concepts") or [] if c.get("prompt")]
        pick = [int(i) - 1 for i in plan.get("chosen") or [1] if 0 < int(i) <= len(ideas)] or [0]
        c = dict(ideas[pick[0]], standalone=True, form="picture")
        c["title"] = str(c.get("title") or c["idea"])[:80]
        c["caption"] = c["idea"]
    except Exception as exc:
        return stop(f"no gallery idea ({type(exc).__name__}: {str(exc)[:200]}).")
    slug = today() + "-picture-" + re.sub(r"[^a-z0-9]+", "-", c["title"].lower()).strip("-")[:50]
    make(ROOT / "pilot" / f"{slug}.md", commission=c)
    return promote([slug])


def promote(slugs: list) -> int:
    """Hang pilot pictures that a person has approved. Draws nothing and
    costs nothing: it moves the files and writes the front matter."""
    import shutil
    rows = load(PILOT_MANIFEST, [])
    keep, hung = [], load(MANIFEST, [])
    OUT.mkdir(parents=True, exist_ok=True)
    for r in rows:
        if slugs and r.get("slug") not in slugs:
            keep.append(r)
            continue
        post = ROOT / r["post"]
        if not r.get("standalone") and not post.exists():
            say(f"no such post, left in the pilot: {r['post']}")
            keep.append(r)
            continue
        if r.get("standalone"):
            for k in ("file", "card", "thumb"):
                shutil.move(str(PILOT_OUT / r[k]), str(OUT / r[k]))
            hung = [m for m in hung if m.get("slug") != r["slug"]] + [r]
            say(f"hung {r['file']} in the gallery")
            continue
        for k in ("file", "card", "thumb"):
            shutil.move(str(PILOT_OUT / r[k]), str(OUT / r[k]))
        set_artwork(post, r)
        hung = [m for m in hung if m.get("slug") != r["slug"]] + [r]
        say(f"hung {r['file']} on {r['post']}")
    save(MANIFEST, hung)
    save(PILOT_MANIFEST, keep)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="append", default=[])
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--force", action="store_true", help="ignore the form list and replace an existing picture")
    ap.add_argument("--candidates", type=int, default=0)
    ap.add_argument("--pilot", action="store_true", help="draw, but hang nothing: files go to pilot/art/")
    ap.add_argument("--commissions", action="store_true",
                    help="draw every picture in pilot/commissions.json that has not been drawn yet")
    ap.add_argument("--gallery", action="store_true", help="make one picture for the gallery, if one is due")
    ap.add_argument("--promote", nargs="*", default=None, metavar="SLUG",
                    help="hang approved pilot pictures (all of them, or the slugs named)")
    a = ap.parse_args()
    if a.promote is not None:
        return promote(a.promote)
    if a.gallery:
        return gallery()
    if a.commissions:
        done = {r.get("slug") for r in load(PILOT_MANIFEST, []) + load(MANIFEST, [])}
        for slug, c in load(COMMISSIONS, {}).items():
            if slug not in done:
                make(ROOT / c.get("post", f"src/posts/{slug}.md"), pilot=True, commission=c)
        return 0
    posts = [pathlib.Path(p) if os.path.isabs(p) else ROOT / p for p in a.post]
    if a.latest:
        latest = load(LATEST, {})
        slug = str(latest.get("url") or "").rstrip("/").split("/")[-1]
        if slug:
            posts.append(ROOT / "src" / "posts" / f"{slug}.md")
    if not posts:
        return stop("no post named.")
    for p in posts:
        make(p, force=a.force, candidates=a.candidates, pilot=a.pilot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
