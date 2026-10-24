"""Evaluate the solver on saved search results without network access."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter


BENCHMARKS = Path(__file__).resolve().parent
PROJECT = BENCHMARKS.parent
CATEGORIES = ('history', 'mathematics', 'literature', 'general')


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(categories: list[str], snapshots_path: Path) -> tuple[list[dict], dict]:
    snapshot = read_json(snapshots_path)
    if snapshot.get('schema_version') != 1 or not isinstance(snapshot.get('items'), dict):
        raise ValueError('Unsupported search snapshot format')
    cases = []
    seen = set()
    for category in categories:
        questions = read_json(BENCHMARKS / 'datasets' / f'{category}.json')
        if not isinstance(questions, list) or len(questions) != 25:
            raise ValueError(f'{category}: expected exactly 25 questions')
        for question in questions:
            qid = question['id']
            answers = question['answers']
            correct = question['correct_index']
            if not isinstance(qid, str) or not qid or qid in seen:
                raise ValueError(f'Invalid or duplicate question ID: {qid!r}')
            seen.add(qid)
            if not isinstance(question['question'], str) or not question['question'].strip():
                raise ValueError(f'{qid}: question must be a nonempty string')
            if (not isinstance(answers, list) or len(answers) != 4
                    or any(not isinstance(a, str) or not a.strip() for a in answers)
                    or len(set(answers)) != 4
                    or type(correct) is not int or not 0 <= correct < 4):
                raise ValueError(f'{qid}: expected four distinct answers and a valid correct_index')
            item = snapshot['items'].get(qid)
            if not isinstance(item, dict):
                raise ValueError(f'{qid}: missing search snapshot')
            if item.get('query') != question['question']:
                raise ValueError(f'{qid}: snapshot query differs from the dataset question')
            if not isinstance(item.get('captured_at'), str):
                raise ValueError(f'{qid}: missing snapshot capture timestamp')
            results = item.get('results')
            if not isinstance(results, list) or any(
                not isinstance(result, dict)
                or any(not isinstance(result.get(key), str) for key in ('title', 'body', 'href'))
                for result in results
            ):
                raise ValueError(f'{qid}: invalid search results')
            cases.append({'category': category, 'data': question, 'results': results})
    return cases, snapshot['settings']


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    answered = sum(row['answered'] for row in rows)
    correct = sum(row['correct'] for row in rows)
    return {
        'questions': total,
        'answered': answered,
        'correct': correct,
        'accuracy': correct / total,
        'coverage': answered / total,
        'selective_accuracy': correct / answered if answered else None,
        'latency_ms': sum(row['latency_ms'] for row in rows) / total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--category', choices=CATEGORIES, nargs='+', default=list(CATEGORIES))
    parser.add_argument('--snapshots', type=Path, default=BENCHMARKS / 'snapshots/search_results.json')
    args = parser.parse_args()
    categories = list(dict.fromkeys(args.category))
    try:
        cases, settings = load_cases(categories, args.snapshots)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))

    # This function imports only matching code; it never imports or calls DDGS.
    sys.path.insert(0, str(PROJECT))
    from core.solver import solve_from_results

    input_paths = [BENCHMARKS / 'datasets' / f'{category}.json' for category in categories]
    hashes = {f'datasets/{path.name}': sha256(path) for path in input_paths}
    hashes['snapshots'] = sha256(args.snapshots)
    hashes['core/solver.py'] = sha256(PROJECT / 'core/solver.py')
    hashes['core/matching.py'] = sha256(PROJECT / 'core/matching.py')
    hashes['core/ranking.py'] = sha256(PROJECT / 'core/ranking.py')

    rows = []
    for case in cases:
        question = case['data']
        start = perf_counter()
        prediction = solve_from_results(
            results=case['results'],
            question=question['question'],
            answers=question['answers'],
        )
        elapsed_ms = (perf_counter() - start) * 1000
        index = prediction['index']
        rows.append({
            'id': question['id'],
            'category': case['category'],
            'question': question['question'],
            'expected_index': question['correct_index'],
            'expected_answer': question['answers'][question['correct_index']],
            'prediction': prediction,
            'answered': index is not None,
            'correct': index == question['correct_index'],
            'latency_ms': elapsed_ms,
            'search_results_count': len(case['results']),
        })

    now = datetime.now(timezone.utc)
    report = {
        'schema_version': 1,
        'created_at': now.isoformat(),
        'mode': 'offline',
        'python_version': sys.version,
        'input_sha256': hashes,
        'capture_settings': settings,
        'overall': summarize(rows),
        'categories': {
            category: summarize([row for row in rows if row['category'] == category])
            for category in categories
        },
        'questions': rows,
    }
    output = BENCHMARKS / 'results' / f'{now:%Y%m%dT%H%M%S%fZ}.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'overall': report['overall'], 'categories': report['categories']},
                     ensure_ascii=False, indent=2))
    print(f'Report: {output}')


if __name__ == '__main__':
    main()
