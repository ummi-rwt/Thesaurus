import json
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path("data/raw/kaikki_french.jsonl")
DB = Path("data/thesaurus.db")

SCHEMA = """
DROP TABLE IF EXISTS translations;
DROP TABLE IF EXISTS forms;
DROP TABLE IF EXISTS words;
CREATE TABLE words (id INTEGER PRIMARY KEY, word TEXT, lang TEXT, pos TEXT);
CREATE TABLE translations (
    id INTEGER PRIMARY KEY, word_id INTEGER, gloss TEXT,
    context TEXT, tags TEXT, rank INTEGER
);
CREATE TABLE forms (
    id INTEGER PRIMARY KEY, form TEXT, lemma TEXT,
    pos TEXT, kind TEXT, description TEXT
);
"""


def main():
    start = time.time()
    words, trans, forms = [], [], []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            word, pos = e.get("word"), e.get("pos")
            if not word:
                continue
            lemma_senses = []
            for s in e.get("senses", []):
                glosses = s.get("glosses")
                if not glosses:
                    continue
                target = s.get("form_of") or s.get("alt_of")
                if target and target[0].get("word"):
                    kind = "form_of" if s.get("form_of") else "alt_of"
                    forms.append((word, target[0]["word"], pos, kind, glosses[-1]))
                elif not target:
                    lemma_senses.append(s)
            if not lemma_senses:
                continue
            wid = len(words) + 1
            words.append((wid, word, e.get("lang_code"), pos))
            seen = set()
            for s in lemma_senses:
                g = s["glosses"]
                if g[-1] in seen:
                    continue
                seen.add(g[-1])
                context = g[0] if len(g) > 1 else None
                tags = ",".join(s.get("tags", []))
                trans.append((wid, g[-1], context, tags, len(seen)))
    print(f"Lecture : {time.time() - start:.0f} s")

    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO words VALUES (?, ?, ?, ?)", words)
    con.executemany(
        "INSERT INTO translations (word_id, gloss, context, tags, rank) VALUES (?, ?, ?, ?, ?)",
        trans,
    )
    con.executemany(
        "INSERT INTO forms (form, lemma, pos, kind, description) VALUES (?, ?, ?, ?, ?)",
        forms,
    )
    con.execute("CREATE INDEX idx_words_word ON words(word)")
    con.execute("CREATE INDEX idx_trans_word ON translations(word_id)")
    con.execute("CREATE INDEX idx_forms_form ON forms(form)")
    con.commit()

    print(f"words : {len(words):,} | translations : {len(trans):,} | forms : {len(forms):,}")
    for w in ("manger", "mangeons", "frange"):
        print(f"\n=== {w} ===")
        for pos, gloss in con.execute(
            "SELECT w.pos, t.gloss FROM words w JOIN translations t ON t.word_id = w.id "
            "WHERE w.word = ? ORDER BY w.id, t.rank LIMIT 6", (w,)
        ):
            print(f"  [{pos}] {gloss}")
        for lemma, desc in con.execute(
            "SELECT lemma, description FROM forms WHERE form = ? LIMIT 4", (w,)
        ):
            print(f"  forme de '{lemma}' : {desc}")
    con.close()
    print(f"\nTermine en {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()
