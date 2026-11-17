import bz2
import csv
import sys
import tarfile
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAW = Path("data/raw")
CLEAN = Path("data/clean")
MAX_LEN = 300


def clean_text(text):
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.split())


def read_sentences(name):
    sentences, malformed = {}, 0
    with bz2.open(RAW / name, "rt", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t", 2)
            if len(parts) != 3:
                malformed += 1
                continue
            sentences[parts[0]] = parts[2]
    print(f"{name} : {len(sentences):,} phrases, {malformed:,} lignes mal formees")
    return sentences


def read_links(fr, en):
    pairs, total = [], 0
    with tarfile.open(RAW / "links.tar.bz2", "r:bz2") as tar:
        f = tar.extractfile(tar.getmembers()[0])
        for line in f:
            total += 1
            parts = line.decode("utf-8").rstrip("\n").split("\t")
            if len(parts) != 2:
                continue
            a, b = parts
            if a in fr and b in en:
                pairs.append((a, b))
    print(f"links : {total:,} lignes lues, {len(pairs):,} paires FR->EN")
    return pairs


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    fr = read_sentences("fra_sentences.tsv.bz2")
    en = read_sentences("eng_sentences.tsv.bz2")
    pairs = read_links(fr, en)

    seen, kept = set(), []
    dropped_empty = dropped_long = dropped_dup = 0
    for fr_id, en_id in pairs:
        fr_text = clean_text(fr[fr_id])
        en_text = clean_text(en[en_id])
        if not fr_text or not en_text:
            dropped_empty += 1
            continue
        if len(fr_text) > MAX_LEN or len(en_text) > MAX_LEN:
            dropped_long += 1
            continue
        key = (fr_text, en_text)
        if key in seen:
            dropped_dup += 1
            continue
        seen.add(key)
        kept.append((fr_id, en_id, fr_text, en_text))

    out = CLEAN / "fr_en_pairs.tsv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["fr_id", "en_id", "fr_text", "en_text"])
        writer.writerows(kept)

    print("\n--- Bilan du nettoyage ---")
    print(f"Paires avant nettoyage : {len(pairs):,}")
    print(f"Supprimees (vides)     : {dropped_empty:,}")
    print(f"Supprimees (trop longues) : {dropped_long:,}")
    print(f"Supprimees (doublons)  : {dropped_dup:,}")
    print(f"Paires conservees      : {len(kept):,}")
    print(f"Fichier ecrit : {out}")


if __name__ == "__main__":
    main()
