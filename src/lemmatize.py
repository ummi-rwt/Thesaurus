import csv
import sys
import time
from pathlib import Path

import spacy

sys.stdout.reconfigure(encoding="utf-8")
CLEAN = Path("data/clean")
SRC = CLEAN / "fr_en_pairs.tsv"
OUT = CLEAN / "fr_en_lemmas.tsv"


def lemmas(nlp, texts, label):
    result = []
    start = time.time()
    for i, doc in enumerate(nlp.pipe(texts, batch_size=1000, n_process=4), start=1):
        result.append(" ".join(
            t.lemma_.lower() for t in doc if not t.is_punct and not t.is_space
        ))
        if i % 50000 == 0:
            print(f"  {label} : {i:,} phrases ({time.time() - start:.0f} s)")
    print(f"{label} termine : {len(result):,} phrases en {time.time() - start:.0f} s")
    return result


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    with open(SRC, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        rows = list(reader)
    if limit:
        rows = rows[:limit]
    print(f"{len(rows):,} paires a lemmatiser")

    nlp_fr = spacy.load("fr_core_news_md", disable=["parser", "ner"])
    nlp_en = spacy.load("en_core_web_sm", disable=["parser", "ner"])

    fr_lem = lemmas(nlp_fr, [r[2] for r in rows], "FR")
    en_lem = lemmas(nlp_en, [r[3] for r in rows], "EN")

    out = OUT if not limit else CLEAN / "fr_en_lemmas_sample.tsv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header + ["fr_lemmas", "en_lemmas"])
        for r, fl, el in zip(rows, fr_lem, en_lem):
            writer.writerow(r + [fl, el])

    print(f"\nFichier ecrit : {out}")
    for r, fl, el in list(zip(rows, fr_lem, en_lem))[:3]:
        print(f"\n{r[2]}\n  -> {fl}\n{r[3]}\n  -> {el}")


if __name__ == "__main__":
    main()
