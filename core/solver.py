from core.ranking import rank_answers

def solve_text_question(
        question: str,
        answers: list[str],
) -> dict:
    from core.search import search

    return solve_from_results(
        results=search(question),
        question=question,
        answers=answers,
    )


def solve_from_results(
        results: list[dict],
        question: str,
        answers: list[str],
) -> dict:
    scores = rank_answers(results, question, answers)
    ordered = sorted(scores, reverse=True)
    if not ordered or ordered[0] <= 0 or (len(ordered) > 1 and ordered[0] - max(0, ordered[1]) <= ordered[0] * 0.05):
        return {
            'answer': None,
            'index': None,
            'confidence': 0.0,
        }

    best = max(range(len(scores)), key=lambda i: scores[i])

    return {
        'answer': answers[best],
        'index': best,
        'confidence': scores[best] / sum(max(0, score) for score in scores),
    }

