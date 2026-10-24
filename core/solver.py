from core.ranking import rank_answers

def solve_text_question(
        question: str,
        answers: list[str],
        timeout: int = 20,
        backend: str = 'auto',
        max_results: int = 1,
        confidence_gap: float = 0.1,
) -> dict:
    from core.search import search

    return solve_from_results(
        results=search(question, timeout=timeout, backend=backend),
        question=question,
        answers=answers,
        max_results=max_results,
        confidence_gap=confidence_gap,
    )


def solve_from_results(
        results: list[dict],
        question: str,
        answers: list[str],
        max_results: int = 1,
        confidence_gap: float = 0.1,
) -> dict:
    scores = rank_answers(results, question, answers)
    ordered = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    total = sum(max(0, score) for score in scores)
    candidates = []
    if total > 0:
        top_confidence = scores[ordered[0]] / total
        for i in ordered:
            confidence = scores[i] / total
            if scores[i] > 0 and top_confidence - confidence <= confidence_gap + 1e-12:
                candidates.append({
                    'answer': answers[i],
                    'index': i,
                    'confidence': confidence,
                })
            if len(candidates) >= max_results:
                break

    if not ordered or scores[ordered[0]] <= 0 or (
        len(ordered) > 1 and scores[ordered[0]] - max(0, scores[ordered[1]]) <= scores[ordered[0]] * 0.05
    ):
        return {
            'answer': None,
            'index': None,
            'confidence': 0.0,
            'candidates': candidates if max_results > 1 else [],
        }

    best = ordered[0]

    return {
        'answer': answers[best],
        'index': best,
        'confidence': scores[best] / total,
        'candidates': candidates,
    }

