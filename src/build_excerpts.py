import sqlite3
import sys
from pathlib import Path

import spacy

from subtitles import read_srt

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path("data/raw/tos")
DB = Path("data/thesaurus.db")
FILM = "tears-of-steel"
MIN_OVERLAP = 0.5

SCHEMA = """
DROP TABLE IF EXISTS excerpts_fts;
DROP TABLE IF EXISTS excerpts;
CREATE TABLE excerpts (
    id INTEGER PRIMARY KEY, film TEXT,
    start_ms INTEGER, end_ms INTEGER,
    fr_text TEXT, en_text TEXT, fr_lemmas TEXT, en_lemmas TEXT
);
"""


def overlap(a, b):
    return max(0, min(a["end_ms"], b["end_ms"]) - max(a["start_ms"], b["start_ms"]))


def align(fr, en):
    pairs, used, exact, lost_fr = [], set(), 0, []
    for f in fr:
        best, best_ov = None, 0
        for j, e in enumerate(en):
            if j in used:
                continue
            ov = overlap(f, e)
            if ov > best_ov:
                best, best_ov = j, ov
        if best is None:
            lost_fr.append(f)
            continue
        e = en[best]
        shortest = min(f["end_ms"] - f["start_ms"], e["end_ms"] - e["start_ms"])
        if best_ov >= MIN_OVERLAP * shortest:
            used.add(best)
            pairs.append((f, e))
            if f["start_ms"] == e["start_ms"] and f["end_ms"] == e["end_ms"]:
                exact += 1
        else:
            lost_fr.append(f)
    lost_en = [e for j, e in enumerate(en) if j not in used]
    return pairs, exact, lost_fr, lost_en


def lemmas(nlp, texts):
    return [
        " ".join(t.lemma_.lower() for t in doc if not t.is_punct and not t.is_space)
        for doc in nlp.pipe(texts)
    ]


def show(con, word, lang):
    cols = "{fr_text fr_lemmas}" if lang == "fr" else "{en_text en_lemmas}"
    rows = con.execute(
        """SELECT e.start_ms, e.end_ms, e.fr_text, e.en_text
           FROM excerpts_fts JOIN excerpts e ON e.id = excerpts_fts.rowid
           WHERE excerpts_fts MATCH ? ORDER BY e.start_ms LIMIT 3""",
        (f'{cols} : "{word}"',),
    ).fetchall()
    print(f"\n=== '{word}' ({lang}) : {len(rows)} extrait(s) affiche(s) ===")
    for s, e, fr, en in rows:
        print(f"  [{s / 1000:.1f}s -> {e / 1000:.1f}s]")
        print(f"    FR : {fr}")
        print(f"    EN : {en}")


def main():
    fr = read_srt(SRC / "TOS-fr-Goofy.srt")
    en = read_srt(SRC / "TOS-en.srt")
    pairs, exact, lost_fr, lost_en = align(fr, en)
    print(f"FR : {len(fr)} repliques | EN : {len(en)} repliques")
    print(f"Paires alignees : {len(pairs)} (minutages identiques : {exact})")
    print(f"Sans correspondance : {len(lost_fr)} FR, {len(lost_en)} EN")

    nlp_fr = spacy.load("fr_core_news_md", disable=["parser", "ner"])
    nlp_en = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    fr_lem = lemmas(nlp_fr, [f["text"] for f, _ in pairs])
    en_lem = lemmas(nlp_en, [e["text"] for _, e in pairs])

    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.executemany(
        "INSERT INTO excerpts (film, start_ms, end_ms, fr_text, en_text, fr_lemmas, en_lemmas) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (FILM, min(f["start_ms"], e["start_ms"]), max(f["end_ms"], e["end_ms"]),
             f["text"], e["text"], fl, el)
            for (f, e), fl, el in zip(pairs, fr_lem, en_lem)
        ],
    )
    con.execute("""
        CREATE VIRTUAL TABLE excerpts_fts USING fts5(
            fr_text, en_text, fr_lemmas, en_lemmas,
            content='excerpts', content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        )
    """)
    con.execute("INSERT INTO excerpts_fts(excerpts_fts) VALUES('rebuild')")
    con.commit()
    print(f"\n{len(pairs)} extraits ranges dans {DB}")

    show(con, "peur", "fr")
    show(con, "espace", "fr")
    show(con, "robot", "en")
    con.close()


if __name__ == "__main__":
    main()
