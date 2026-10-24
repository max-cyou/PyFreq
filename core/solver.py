from core.search import search
from core.matching import count_occurrences

def solve_text_question(
        question: str,
        answers: list[str],
) -> dict:

    results = search(question)

    scores = [0] * len(answers)

    for result in results:
        text = ' '.join([
            result.get('title', ''),
            result.get('body', ''),
        ])

        for i, answer in enumerate(answers):
            scores[i] += count_occurrences(text, answer)

    if not any(scores):
        return {
            'answer': None,
            'index': None,
            'confidence': 0.0,
        }

    best = max(range(len(scores)), key=lambda i: scores[i])

    return {
        'answer': answers[best],
        'index': best,
        'confidence': scores[best] / sum(scores),
    }

