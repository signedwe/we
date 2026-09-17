"""Style report for a WE page before it is published.

  python _claude-publish/style.py path/to/page.md [more.md ...]

Runs the plain-English checks from agent/plain.py over the whole page: the
body, every proposal, every voice. Prints a scorecard per section and the
failures in the writer's own words. Exit code 1 if anything fails, so it can
sit in a script. Quoted spans are ignored, so a source's jargon can be quoted.
"""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agent"))
import yaml
from plain import check_plain, scorecard

def sections(path):
    src = open(path, encoding="utf-8").read()
    _, fm, body = src.split("---\n", 2)
    meta = yaml.safe_load(fm) or {}
    yield "body", body
    for p in meta.get("proposals", []) or []:
        by = p.get("by", "")
        if "human" in by.lower():
            continue  # the human's own words are not WE's to tidy
        yield f"proposal: {by[:50]}", p.get("text", "")
    for v in (meta.get("responses") or meta.get("voices") or []):
        yield f"voice: {v.get('thinker') or v.get('kind')}", v.get("argument", "")

bad = 0
for path in sys.argv[1:]:
    print(f"\n== {path}")
    whole = []
    for name, text in sections(path):
        whole.append(text)
        fails = check_plain(text)
        flag = "FAIL" if fails else "ok  "
        print(f"{flag} {name}: {scorecard(text)}")
        for f in fails:
            print(f"      - {f}")
        bad += bool(fails)
    print("PAGE:", scorecard("\n".join(whole)))
sys.exit(1 if bad else 0)
