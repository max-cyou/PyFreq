import re
from functools import lru_cache

from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer()

@lru_cache(maxsize=10000)
def lemmatize(word: str) -> str:
    return morph.parse(word)[0].normal_form.replace('ё', 'е')

def normalize(text: str) -> str:
    text = text.lower().replace('ё', 'е')
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(lemmatize(word) for word in text.split())

def count_occurrences(text: str, answer: str) -> int:
    text = normalize(text)
    answer = normalize(answer)

    if not answer:
        return 0

    pattern = rf'(?<!\w){re.escape(answer)}(?!\w)'

    return len(re.findall(pattern, text))

