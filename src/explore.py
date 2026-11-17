import bz2
import sys
import tarfile
from itertools import islice
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAW = Path("data/raw")


def peek_sentences(name):
    print(f"\n=== {name} ===")
    with bz2.open(RAW / name, "rt", encoding="utf-8") as f:
        for line in islice(f, 5):
            print(repr(line))
    with bz2.open(RAW / name, "rt", encoding="utf-8") as f:
        total = sum(1 for _ in f)
    print(f"Nombre de lignes : {total:,}")


def peek_links():
    print("\n=== links.tar.bz2 ===")
    with tarfile.open(RAW / "links.tar.bz2", "r:bz2") as tar:
        member = tar.getmembers()[0]
        print(f"Fichier dans l'archive : {member.name}")
        f = tar.extractfile(member)
        for line in islice(f, 5):
            print(repr(line.decode("utf-8")))
    with tarfile.open(RAW / "links.tar.bz2", "r:bz2") as tar:
        f = tar.extractfile(tar.getmembers()[0])
        total = sum(1 for _ in f)
    print(f"Nombre de lignes : {total:,}")


if __name__ == "__main__":
    peek_sentences("fra_sentences.tsv.bz2")
    peek_sentences("eng_sentences.tsv.bz2")
    peek_links()
