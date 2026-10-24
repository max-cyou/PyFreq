import re
from collections import Counter
from functools import lru_cache
from html import unescape
from math import log

from core.matching import count_occurrences, lemmatize, morph, normalize_latex, normalize_math


@lru_cache(maxsize=10000)
def word_info(word: str) -> tuple[str, str | None, bool]:
    parsed = morph.parse(word)[0]
    return parsed.normal_form.replace('ё', 'е'), parsed.tag.POS, 'Apro' in parsed.tag


@lru_cache(maxsize=10000)
def words(text: str) -> list[str]:
    return [lemmatize(word) for word in re.findall(r'\w+', normalize_math(text))]


@lru_cache(maxsize=10000)
def terms(text: str) -> set[str]:
    result = set()
    for word in re.findall(r'\w+', normalize_math(text)):
        lemma, pos, pronoun = word_info(word)
        if pos not in {'PREP', 'CONJ', 'PRCL', 'NPRO', 'INTJ'} and not pronoun:
            result.add(lemma)
    return result


def contexts(result: dict) -> list[tuple[str, str]]:
    title = unescape(result.get('title', ''))
    body = normalize_latex(result.get('body', ''))
    body = re.sub(r'</?(?:p|div|span|br|a|b|i|strong|em)\b[^>]*>', ' ', body, flags=re.I)
    sentences = [part.strip() for part in re.split(r'(?<=[.!?;])\s+|[\n;]+', body) if part.strip()]
    fragments = [(title, title)] if title.strip() else []
    for i, sentence in enumerate(sentences):
        neighbours = ' '.join(sentences[max(0, i - 1):i + 2])
        fragments.append((sentence, title + ' ' + neighbours))
    return fragments


def negations(tokens: list[str]) -> list[int]:
    return [i for i, word in enumerate(tokens)
            if word in {'не', 'ни', 'нет'}
            and not (word == 'не' and i + 1 < len(tokens) and tokens[i + 1] == 'только')]


def polarity(question: str, answer: str, context: str) -> int:
    if context.rstrip().endswith('?'):
        return 0
    if context.count('=') == 1:
        left, right = context.split('=')
        query = terms(question)
        overlap_left = len(query & terms(left))
        overlap_right = len(query & terms(right))
        if overlap_left != overlap_right:
            given, value = (left, right) if overlap_left > overlap_right else (right, left)
            if count_occurrences(given, answer) and not count_occurrences(value, answer):
                return 0
    parts = re.split(r'[,;]\s*(?=(?:а|но|однако)\b)', context, flags=re.I)
    matching = [part for part in parts if count_occurrences(part, answer)]
    if len(matching) != 1:
        return 0
    tokens = words(matching[0])
    negative = negations(tokens)
    if negative:
        # Multiple predicates make the scope ambiguous without a dependency parser.
        predicates = [word for word in re.findall(r'\w+', matching[0].lower())
                      if word_info(word)[1] in {'VERB', 'PRTS', 'ADJS', 'PRED'}]
        if len(predicates) > 1:
            return 0
        # "не только" is additive; nested and repeated negations are ambiguous.
        if len(negative) > 1 and not all(tokens[i] == 'ни' for i in negative[1:]):
            return 0
    return 1 if bool(negative) == bool(negations(words(question))) else -1


def rank_answers(results: list[dict], question: str, answers: list[str]) -> list[float]:
    documents = []
    seen_urls, seen_documents = set(), set()
    for result in results:
        url = (result.get('href') or '').split('#')[0]
        fragments = contexts(result)
        identity = tuple(normalize_math(fragment) for fragment, _ in fragments)
        if not identity or identity in seen_documents or (url and url in seen_urls):
            continue
        seen_documents.add(identity)
        if url:
            seen_urls.add(url)
        documents.append((len(documents), fragments))

    answer_terms = set().union(*(terms(answer) for answer in answers))
    query = terms(question) - answer_terms
    if not query:
        query = terms(question)
    if not query or not documents:
        return [0.0] * len(answers)

    frequency = Counter()
    for _, fragments in documents:
        frequency.update(set().union(*(terms(context) for _, context in fragments)))
    weights = {term: log(1 + (len(documents) + 1) / (frequency[term] + 1)) for term in query}
    total_weight = sum(weights.values())
    scores = [0.0] * len(answers)
    seen_fragments = set()

    for position, fragments in documents:
        positive, negative = [0.0] * len(answers), [0.0] * len(answers)
        for fragment, context in fragments:
            identity = normalize_math(fragment)
            if identity in seen_fragments:
                continue
            seen_fragments.add(identity)
            local, surrounding = terms(fragment), terms(context)
            local_score = sum(weights[t] for t in query & local) / total_weight
            context_score = sum(weights[t] for t in query & surrounding) / total_weight
            relevance = context_score * (local_score + context_score) / 2
            if relevance <= 0:
                continue
            for i, answer in enumerate(answers):
                if not count_occurrences(fragment, answer):
                    continue
                sign = polarity(question, answer, fragment)
                if sign > 0:
                    positive[i] = max(positive[i], relevance)
                elif sign < 0:
                    negative[i] = max(negative[i], relevance)
        weight = 1 / log(position + 2)
        for i in range(len(answers)):
            scores[i] += weight * (positive[i] - negative[i])
    return scores
