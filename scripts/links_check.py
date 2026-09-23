"""Every Sunday, open every link on /links/ and mark the dead ones.

A list of links rots. This reads src/links.md, requests each URL, and where
one fails twice it appends a note to that line: "(dead when checked on
DATE)". A link that comes back loses the note. Nothing is deleted; the
person who runs this decides what to replace.

Usage:
    python scripts/links_check.py
"""

import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "src" / "links.md"
NOTE = re.compile(r"\s*\*\(dead when checked on \d{4}-\d{2}-\d{2}\)\*\s*$")
UA = "Mozilla/5.0 (compatible; WE link check; +https://signedwe.github.io/we/links/)"


def alive(url: str) -> bool:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status < 400:
                    return True
        except urllib.error.HTTPError as exc:
            # Some sites refuse HEAD and some refuse robots; only a plain
            # 404 or 410 is a dead page. Everything else is treated as alive
            # rather than marking a living page dead.
            if exc.code in (404, 410):
                continue
            return True
        except Exception:
            time.sleep(2)
            continue
    return False


def main() -> int:
    text = PAGE.read_text(encoding="utf-8")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out, dead = [], []
    for line in text.splitlines():
        m = re.match(r"^- \[([^\]]+)\]\((https?://[^)]+)\)", line)
        if not m:
            out.append(line)
            continue
        name, url = m.group(1), m.group(2)
        clean = NOTE.sub("", line)
        if alive(url):
            out.append(clean)
        else:
            dead.append(f"{name}: {url}")
            out.append(f"{clean} *(dead when checked on {today})*")
    new = "\n".join(out) + "\n"
    if new != text:
        PAGE.write_text(new, encoding="utf-8")
    print(f"{len(dead)} dead link(s)" + (": " + "; ".join(dead) if dead else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
