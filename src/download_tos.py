import sys
import urllib.request
from pathlib import Path

from subtitles import read_srt

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://download.blender.org/demo/movies/ToS/subtitles"
FILES = {"en": "TOS-en.srt", "fr": "TOS-fr-Goofy.srt"}
OUT = Path("data/raw/tos")


def download(name):
    dest = OUT / name
    if not dest.exists():
        req = urllib.request.Request(
            f"{BASE}/{name}", headers={"User-Agent": "thesaurus-portfolio-project"}
        )
        with urllib.request.urlopen(req) as resp:
            dest.write_bytes(resp.read())
        print(f"Telecharge : {name}")
    return dest


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, name in FILES.items():
        path = download(name)
        cues = read_srt(path)
        print(f"\n=== {lang} : {name} ({path.stat().st_size} octets) ===")
        print(f"Repliques : {len(cues)}")
        if cues:
            print(f"Du debut a {cues[-1]['end_ms'] / 60000:.1f} min")
            for c in cues[:5]:
                print(f"  {c['start_ms'] / 1000:7.1f}s  {c['text']}")


if __name__ == "__main__":
    main()
