import csv
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
SRC = Path("data/clean/fr_en_lemmas.tsv")
DB = Path("data/thesaurus.db")


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE pairs (
            id INTEGER PRIMARY KEY,
            fr_id INTEGER, en_id INTEGER,
            fr_text TEXT, en_text TEXT,
            fr_lemmas TEXT, en_lemmas TEXT
        )
    """)
    sql = ("INSERT INTO pairs (fr_id, en_id, fr_text, en_text, fr_lemmas, en_lemmas) "
           "VALUES (?, ?, ?, ?, ?, ?)")
    start = time.time()
    total = 0
    with open(SRC, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        batch = []
        for row in reader:
            batch.append(row)
            if len(batch) == 20000:
                con.executemany(sql, batch)
                total += len(batch)
                batch = []
        if batch:
            con.executemany(sql, batch)
            total += len(batch)
    con.commit()
    print(f"{total:,} paires inserees en {time.time() - start:.0f} s")

    print("Construction de l'index de recherche...")
    try:
        con.execute("""
            CREATE VIRTUAL TABLE pairs_fts USING fts5(
                fr_text, en_text, fr_lemmas, en_lemmas,
                content='pairs', content_rowid='id',
                tokenize='unicode61 remove_diacritics 2'
            )
        """)
    except sqlite3.OperationalError as e:
        print(f"FTS5 indisponible : {e}")
        return
    con.execute("INSERT INTO pairs_fts(pairs_fts) VALUES('rebuild')")
    con.commit()
    con.close()
    print(f"Termine en {time.time() - start:.0f} s")
    print(f"Base : {DB} ({DB.stat().st_size / 1e6:.0f} Mo)")


if __name__ == "__main__":
    main()
