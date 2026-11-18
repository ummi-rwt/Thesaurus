import sqlite3
import sys
import time
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
DB = "data/thesaurus.db"
CHECK = ["manger", "bouffer", "ruper", "croûter", "becter", "claper", "affûter", "repaître"]


def main():
    start = time.time()
    con = sqlite3.connect(DB)
    counts, seen = Counter(), set()
    for fr_id, lemmas in con.execute("SELECT fr_id, fr_lemmas FROM pairs"):
        if fr_id in seen:
            continue
        seen.add(fr_id)
        counts.update(set(lemmas.split()))
    print(f"{len(seen):,} phrases francaises distinctes, {len(counts):,} lemmes differents")

    con.execute("DROP TABLE IF EXISTS word_freq")
    con.execute("CREATE TABLE word_freq (word TEXT PRIMARY KEY, n INTEGER)")
    con.executemany("INSERT INTO word_freq VALUES (?, ?)", counts.items())
    con.commit()

    print("\nLes 15 lemmes les plus frequents :")
    for w, n in counts.most_common(15):
        print(f"  {w:12} {n:,}")
    print("\nVerification :")
    for w in CHECK:
        print(f"  {w:12} {counts.get(w, 0):,}")
    con.close()
    print(f"\nTermine en {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
