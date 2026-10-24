import re

def normalize(text: str) -> str:
    text = text.lower().replace('ё', 'е')
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def count_occurrences(text: str, answer: str) -> int:
    text = normalize(text)
    answer = normalize(answer)

    if not answer:
        return 0

    pattern = rf'(?<!\w){re.escape(answer)}(?!\w)'

    return len(re.findall(pattern, text))

