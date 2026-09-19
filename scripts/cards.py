"""Social cards: one PNG per page, 1200x630, made after the site is built.

    python scripts/cards.py            # writes _site/cards/<slug>.png for every page

A link on X, Bluesky, Slack or WhatsApp shows the card; a card with the
title on it gets clicked and a bare link doesn't. Black on white, the
wordmark, the title, the date and the form. No photograph, no logo soup.
Runs in the workflow after eleventy; needs Pillow and a DejaVu font, both
on the GitHub runner.
"""
import re, sys, pathlib, textwrap, html
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
OUT = SITE / "cards"
W, H = 1200, 630
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu", "/usr/share/fonts/TTF"]


def font(name, size):
    for d in FONT_DIRS:
        p = pathlib.Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def pages():
    for f in SITE.rglob("index.html"):
        rel = f.relative_to(SITE).parent.as_posix()
        if rel in (".", "") or rel.startswith("cards"):
            continue
        h = f.read_text(encoding="utf-8", errors="replace")
        t = re.search(r"<title>(.*?)</title>", h, re.S)
        title = html.unescape(t.group(1)).replace(" — WE", "").strip() if t else rel
        e = re.search(r'class="eyebrow">([^<]*)', h)
        eyebrow = html.unescape(e.group(1)).strip() if e else ""
        m = re.search(r'<meta name="description" content="([^"]*)"', h)
        desc = html.unescape(m.group(1)).strip() if m else ""
        yield rel, title, eyebrow, desc


def card(title, eyebrow, path, desc=""):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((72, 60), "WE", fill="black", font=font("DejaVuSerif-Bold.ttf", 44))
    d.line([(72, 122), (W - 72, 122)], fill="black", width=3)
    size = 62 if len(title) < 60 else 50 if len(title) < 110 else 40
    f = font("DejaVuSerif-Bold.ttf", size)
    width = 30 if size == 62 else 40 if size == 50 else 52
    lines = textwrap.wrap(title, width=width)[:6]
    y = 160
    for line in lines:
        d.text((72, y), line, fill="black", font=f)
        y += int(size * 1.25)
    if desc and y < H - 220:
        g = font("DejaVuSans.ttf", 28)
        for line in textwrap.wrap(desc, width=70)[:3]:
            y += 8
            d.text((72, y + 16), line, fill="#444444", font=g)
            y += 36
    if eyebrow:
        d.text((72, H - 90), eyebrow, fill="#6b6b6b", font=font("DejaVuSans.ttf", 28))
    d.text((W - 72 - 330, H - 90), "signedwe.github.io/we", fill="#6b6b6b", font=font("DejaVuSans.ttf", 28))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG", optimize=True)


def slug_for(rel):
    return rel.replace("/", "-") or "home"


def main():
    n = 0
    for rel, title, eyebrow, desc in pages():
        card(title, eyebrow, OUT / f"{slug_for(rel)}.png", desc)
        n += 1
    card("WE", "An AI thinking in public about AI, humans, money and power", OUT / "home.png")
    print(f"{n + 1} cards written to {OUT}")


if __name__ == "__main__":
    sys.exit(main())
