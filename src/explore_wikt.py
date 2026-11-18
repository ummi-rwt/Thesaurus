import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path("data/raw/kaikki_french.jsonl")
TARGETS = {"manger", "mangeons", "frange"}


def is_form(senses):
    return bool(senses) and all("form_of" in s or "alt_of" in s for s in senses)


def main():
    entries = form_entries = no_gloss = 0
    pos_count, lang_count, keys_seen = Counter(), Counter(), Counter()
    samples = {}
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            entries += 1
            pos_count[e.get("pos")] += 1
            lang_count[e.get("lang_code")] += 1
            keys_seen.update(e.keys())
            senses = e.get("senses", [])
            if is_form(senses):
                form_entries += 1
            if not any(s.get("glosses") for s in senses):
                no_gloss += 1
            w = e.get("word")
            if w in TARGETS:
                samples.setdefault(w, []).append(e)

    print(f"Entrees : {entries:,}")
    print(f"Formes conjuguees/accordees (form_of) : {form_entries:,}")
    print(f"Entrees sans aucune definition : {no_gloss:,}")
    print(f"Langues : {dict(lang_count)}")
    print("\nCategories grammaticales :")
    for pos, n in pos_count.most_common(8):
        print(f"  {pos:12} {n:,}")
    print("\nChamps les plus frequents :")
    for k, n in keys_seen.most_common(15):
        print(f"  {k:20} {n:,}")

    for w in ("manger", "mangeons", "frange"):
        print(f"\n===== {w} =====")
        for e in samples.get(w, []):
            forms = [x.get("form") for x in e.get("forms", [])]
            print(f"- pos={e.get('pos')} | {len(forms)} formes, ex. {forms[:4]}")
            for s in e.get("senses", [])[:3]:
                print(f"    glosses={s.get('glosses')} form_of={s.get('form_of')}")


if __name__ == "__main__":
    main()
