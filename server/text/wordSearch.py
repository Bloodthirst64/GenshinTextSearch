import re
from functools import lru_cache
from lemminflect import getLemma, getAllInflections


@lru_cache(maxsize=1024)
def expand_word_forms(word):
    forms = set()
    forms.add(word.lower())

    for upos in ['NOUN', 'VERB', 'ADJ', 'ADV']:
        try:
            lemmas = getLemma(word, upos, lemmatize_oov=False)
            for lemma in lemmas:
                inflections = getAllInflections(lemma)
                for tag, spellings in inflections.items():
                    for spelling in spellings:
                        forms.add(spelling.lower())
        except Exception:
            continue

    return list(forms)


@lru_cache(maxsize=512)
def _expand_query_words_cached(query):
    words = query.strip().split()
    result = []
    for word in words:
        forms = expand_word_forms(word.lower())
        if len(forms) == 1 and forms[0] == word.lower():
            pass
        result.append(tuple(forms))
    return tuple(result)


def expand_query_words(query):
    return [list(forms) for forms in _expand_query_words_cached(query.lower())]
