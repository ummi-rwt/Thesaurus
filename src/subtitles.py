import re
from pathlib import Path

TIME = re.compile(
    r"(\d+):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d+):(\d{2}):(\d{2})[,.](\d{3})"
)
TAG = re.compile(r"<[^>]+>|\{\\[^}]*\}")


def to_ms(h, m, s, ms):
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms)


def parse_srt(text):
    """Retourne une liste de {start_ms, end_ms, text}."""
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        for i, line in enumerate(lines):
            m = TIME.search(line)
            if not m:
                continue
            g = m.groups()
            start, end = to_ms(*g[:4]), to_ms(*g[4:])
            body = " ".join(TAG.sub("", part).strip() for part in lines[i + 1:])
            body = " ".join(body.split())
            if body and end > start:
                cues.append({"start_ms": start, "end_ms": end, "text": body})
            break
    return cues


def read_srt(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return parse_srt(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return parse_srt(raw.decode("latin-1"))
