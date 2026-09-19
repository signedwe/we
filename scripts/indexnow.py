"""Tell the search engines what changed, the moment it deploys.

    python scripts/indexnow.py            # pages changed in the last commit, plus the home page
    python scripts/indexnow.py --all      # everything in the sitemap (first run, or after a rebuild)

IndexNow is the open protocol Bing, DuckDuckGo, Yandex and Naver share:
one POST with the changed URLs and a key that lives in a file on the site.
No account, no sign-in. Google doesn't take it; Google gets the sitemap.
Runs after deploy. A failure here is loud and harmless.
"""
import json, pathlib, re, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://signedwe.github.io/we"
HOST = "signedwe.github.io"
STATIC = ROOT / "src" / "static"


def key():
    files = sorted(p for p in STATIC.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", p.name))
    if not files:
        sys.exit("No IndexNow key file in src/static (32 hex chars .txt).")
    return files[-1].stem


def url_for(path):
    m = re.match(r"src/(posts|ideas)/(.+)\.md$", path)
    return f"{SITE}/{m.group(1)}/{m.group(2)}/" if m else None


def changed():
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "HEAD~1", "HEAD"], text=True)
    except subprocess.CalledProcessError:
        out = ""
    urls = {u for u in (url_for(p) for p in out.split()) if u}
    return urls


def everything():
    sm = ROOT / "_site" / "sitemap.xml"
    if not sm.exists():
        return set()
    return set(re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8")))


def main():
    k = key()
    urls = everything() if "--all" in sys.argv else changed()
    urls |= {f"{SITE}/", f"{SITE}/sitemap.xml"}
    body = json.dumps({"host": HOST, "key": k, "keyLocation": f"{SITE}/{k}.txt",
                       "urlList": sorted(urls)[:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow: {r.status} for {len(urls)} urls")
    except urllib.error.HTTPError as e:
        print(f"IndexNow refused: {e.code} {e.read()[:200]!r} for {len(urls)} urls")
        return 0 if e.code in (200, 202) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
