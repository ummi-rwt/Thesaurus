import time
import urllib.request
from pathlib import Path

URL = "https://kaikki.org/dictionary/French/kaikki.org-dictionary-French.jsonl"
DEST = Path("data/raw/kaikki_french.jsonl")


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        print(f"Deja present : {DEST} ({DEST.stat().st_size / 1e6:.0f} Mo)")
        return
    tmp = DEST.with_suffix(".part")
    req = urllib.request.Request(URL, headers={"User-Agent": "thesaurus-portfolio-project"})
    start = time.time()
    with urllib.request.urlopen(req) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r{done / 1e6:.0f} / {total / 1e6:.0f} Mo", end="", flush=True)
    tmp.rename(DEST)
    print(f"\nTermine en {time.time() - start:.0f} s : {DEST}")


if __name__ == "__main__":
    main()
