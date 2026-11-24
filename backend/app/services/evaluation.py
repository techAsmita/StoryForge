"""Automatic evaluation of a generated story (syllabus: text generation evaluation metrics).

All metrics are reference-free (a creative story has no single "correct" answer, so BLEU/ROUGE
against a reference would not be meaningful). Each one is simple enough to explain in a viva:

distinct_1 / distinct_2  unique unigrams / bigrams divided by total -> lexical diversity
                         (rises with temperature; repetition lowers it)
brief_coverage           share of content words from the user's brief that appear in the story
                         (a lexical proxy for prompt adherence; paraphrases are not counted)
character_presence       average share of chapters in which each named character appears
                         (a proxy for character consistency)
length_ratio             actual words per chapter / requested words per chapter
structure_score          share of schema checks passed (6 beats, 4 scenes, requested chapter count)
"""
import re

from ..prompts.strategies import length_targets

STOPWORDS = set("""
a an the and or but of to in on at for with by from into onto over under about after before behind
is are was were be been being has have had do does did will would can could should may might must
this that these those it its their his her they them he she you your our we i me my mine not no
every each any all some more most such than then there here when where which who whom whose what
""".split())

WORD = re.compile(r"[a-zA-Z']+")


def _words(text: str) -> list[str]:
    return [w.lower() for w in WORD.findall(text)]


def _distinct(tokens: list[str], n: int) -> float:
    grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    return round(len(set(grams)) / len(grams), 3) if grams else 0.0


def evaluate(story) -> dict:
    out = story.output
    chapters = out.get("chapters", [])
    chapter_texts = [c.get("text", "") for c in chapters]
    full = " ".join([out.get("logline", "")] + chapter_texts)
    tokens = _words(full)
    story_vocab = set(tokens)

    brief_terms = {
        w for field in ("protagonist", "goal", "world_rule", "ending_twist")
        for w in _words(story.idea.get(field, "")) if len(w) > 3 and w not in STOPWORDS
    }
    found = sorted(t for t in brief_terms if t in story_vocab)

    presence = []
    for ch in out.get("characters", []):
        first = _words(ch.get("name", ""))[:1]
        if first and chapter_texts:
            hits = sum(1 for t in chapter_texts if first[0] in set(_words(t)))
            presence.append(hits / len(chapter_texts))

    n_chapters, words_per = length_targets(story.plot.get("length", 60))
    words_total = sum(len(_words(t)) for t in chapter_texts)
    checks = [len(out.get("beats", [])) == 6, len(out.get("scenes", [])) == 4, len(chapters) == n_chapters]

    return {
        "distinct_1": _distinct(tokens, 1),
        "distinct_2": _distinct(tokens, 2),
        "brief_coverage": round(len(found) / len(brief_terms), 3) if brief_terms else None,
        "brief_terms_found": found,
        "brief_terms_missing": sorted(brief_terms - set(found)),
        "character_presence": round(sum(presence) / len(presence), 3) if presence else None,
        "word_count": words_total,
        "length_ratio": round(words_total / (n_chapters * words_per), 2) if chapters else None,
        "structure_score": round(sum(checks) / len(checks), 2),
        "llm_calls": len(story.runs),
        "latency_ms": round(sum(r.latency_ms for r in story.runs)),
    }
