import time
import urllib.request
from pathlib import Path

URLS = [
    "http://ftp.nluug.nl/pub/graphics/blender/demo/movies/ToS/tears_of_steel_720p.mov",
    "http://ftp.halifax.rwth-aachen.de/blender/demo/movies/ToS/tears_of_steel_720p.mov",
]
DEST = Path("data/video/tears_of_steel_720p.mov")
MIN_SIZE = 300_000_000


def fetch(url):
    tmp = DEST.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "thesaurus-portfolio-project"})
    start = time.time()
    done = 0
    with urllib.request.urlopen(req, timeout=60) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r{done / 1e6:.0f} / {total / 1e6:.0f} Mo", end="", flush=True)
    if done < MIN_SIZE:
        raise RuntimeError(f"fichier trop petit : {done} octets")
    tmp.replace(DEST)
    print(f"\nTermine en {time.time() - start:.0f} s : {DEST}")


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.exists():
        print(f"Deja present : {DEST} ({DEST.stat().st_size / 1e6:.0f} Mo)")
        return
    for url in URLS:
        print(f"Essai : {url}")
        try:
            fetch(url)
            return
        except Exception as e:
            print(f"\nEchec : {e}")
    print("Aucun miroir n'a repondu.")


if __name__ == "__main__":
    main()
