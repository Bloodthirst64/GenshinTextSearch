import re
from lemminflect import getLemma, getAllInflections


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


def expand_query_words(query):
    words = query.strip().split()
    result = []
    for word in words:
        forms = expand_word_forms(word)
        if len(forms) == 1 and forms[0] == word.lower():
            pass
        result.append(forms)
    return result
