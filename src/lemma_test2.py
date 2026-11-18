import sys
import spacy

sys.stdout.reconfigure(encoding="utf-8")

phrases = [
    "Essayons quelque chose !",
    "essayons quelque chose !",
    "Mangeons ensemble.",
    "Allons au cinéma.",
]

for model in ["fr_core_news_sm", "fr_core_news_md"]:
    nlp = spacy.load(model, disable=["parser", "ner"])
    print(f"\n=== {model} ===")
    for text in phrases:
        first = nlp(text)[0]
        print(f"{text:28} -> {first.lemma_:10} ({first.pos_})")
