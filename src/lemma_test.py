import sys
import spacy

sys.stdout.reconfigure(encoding="utf-8")

nlp_fr = spacy.load("fr_core_news_sm", disable=["parser", "ner"])
nlp_en = spacy.load("en_core_web_sm", disable=["parser", "ner"])

tests = [
    (nlp_fr, "Nous mangeons des pommes."),
    (nlp_fr, "Essayons quelque chose !"),
    (nlp_en, "She was eating the apples."),
]

for nlp, text in tests:
    print(f"\n{text}")
    for token in nlp(text):
        if not token.is_punct:
            print(f"  {token.text:12} -> {token.lemma_:12} ({token.pos_})")
