from pathlib import Path
import urllib.request

BASE = "https://downloads.tatoeba.org/exports"
FILES = {
    "fra_sentences.tsv.bz2": f"{BASE}/per_language/fra/fra_sentences.tsv.bz2",
    "eng_sentences.tsv.bz2": f"{BASE}/per_language/eng/eng_sentences.tsv.bz2",
    "links.tar.bz2": f"{BASE}/links.tar.bz2",
}
RAW = Path("data/raw")


def download(name, url):
    dest = RAW / name
    if dest.exists():
        print(f"Déjà présent : {name}")
        return
    print(f"Téléchargement : {name}")
    urllib.request.urlretrieve(url, dest)
    print(f"OK : {dest.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        download(name, url)