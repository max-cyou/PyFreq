import re
from functools import lru_cache
from html import unescape

from pymorphy3 import MorphAnalyzer

morph = MorphAnalyzer()

def read_group(text: str, start: int) -> tuple[str | None, int]:
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text) or text[start] != '{':
        return None, start
    depth = 1
    for end in range(start + 1, len(text)):
        if text[end] == '{':
            depth += 1
        elif text[end] == '}':
            depth -= 1
            if not depth:
                return text[start + 1:end], end + 1
    return None, start

def normalize_latex(text: str) -> str:
    text = unescape(text)
    text = re.sub(r'<sup>(.*?)</sup>', r'^(\1)', text, flags=re.I)
    text = re.sub(r'<sub>(.*?)</sub>', r'_(\1)', text, flags=re.I)
    operators = {
        'cdot': '*', 'times': '*', 'div': '/', 'pm': '±',
        'le': '≤', 'leq': '≤', 'ge': '≥', 'geq': '≥', 'ne': '≠', 'neq': '≠',
        'pi': 'π', 'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'theta': 'θ',
        'lambda': 'λ', 'mu': 'μ', 'sigma': 'σ', 'omega': 'ω',
    }
    formatting = {'text', 'textrm', 'mathrm', 'mathbf', 'mathit', 'operatorname'}
    functions = {'sin', 'cos', 'tan', 'tg', 'ctg', 'ln', 'log', 'exp'}
    output = []
    start = 0
    while start < len(text):
        if text[start] == '$':
            start += 1
            continue
        command = re.match(r'\\([a-zA-Z]+|.)', text[start:]) if text[start] == '\\' else None
        if not command:
            output.append({'{': '(', '}': ')'}.get(text[start], text[start]))
            start += 1
            continue
        name = command.group(1)
        end = start + len(command.group())
        if name in {'frac', 'dfrac', 'tfrac'}:
            numerator, middle = read_group(text, end)
            denominator, finish = read_group(text, middle) if numerator is not None else (None, middle)
            if denominator is not None:
                output.append(f'({normalize_latex(numerator)})/({normalize_latex(denominator)})')
                start = finish
                continue
        elif name == 'sqrt' or name in formatting:
            argument, finish = read_group(text, end)
            if argument is not None:
                value = normalize_latex(argument)
                output.append(f'sqrt({value})' if name == 'sqrt' else value)
                start = finish
                continue
        if name in operators:
            output.append(operators[name])
        elif name in functions:
            output.append(name + ' ')
        elif name in {'left', 'right', 'displaystyle', 'textstyle', '(', ')', '[', ']', ',', ';', '!', ' ', '\\'}:
            output.append(' ')
        else:
            output.append(command.group())
        start = end
    return ''.join(output)

@lru_cache(maxsize=10000)
def lemmatize(word: str) -> str:
    return morph.parse(word)[0].normal_form.replace('ё', 'е')

def normalize(text: str) -> str:
    text = normalize_latex(text).lower().replace('ё', 'е')
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(lemmatize(word) for word in text.split())

def normalize_math(text: str) -> str:
    text = normalize_latex(text).lower().translate(str.maketrans('−×·÷∕⁄', '-**///'))
    text = re.sub(
        r'[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+',
        lambda match: '^' + match.group().translate(str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺', '0123456789-+')),
        text,
    )
    text = text.replace('**', '^')
    text = re.sub(r'(?<=\d),(?=\d)', '.', text)
    text = re.sub(r'√\s*([a-zα-ω]|\d+(?:\.\d+)?)', r'sqrt \1', text)
    text = re.sub(r'√\s*\(', 'sqrt(', text)
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r'\(\s*([a-zα-ω]+|\d+(?:\.\d+)?)\s*\)', r' \1 ', text)
    text = re.sub(r'\b(sin|cos|tan|tg|ctg|ln|log)\s*\(\s*([a-z])\s*\)', r'\1 \2', text)
    text = re.sub(r'\b(sin|cos|tan|tg|ctg|ln|log)([a-z])\b', r'\1 \2', text)
    return ' '.join(re.findall(r'\d+(?:\.\d+)?|[^\W\d_]+|[^\w\s]|_', text))

def count_occurrences(text: str, answer: str) -> int:
    math_answer = normalize_math(answer)
    if math_answer and re.fullmatch(r'[a-zα-ω\d\s_.+*/^=()!%√±≤≥≠<>\\-]+', math_answer):
        text = normalize_math(text)
        pattern = rf'(?<![\w.])(?<![+*/^-] ){re.escape(math_answer)}(?![\w.])(?! [+*/^!%-])'
        return len(re.findall(pattern, text))

    text = normalize(text)
    answer = normalize(answer)

    if not answer:
        return 0

    pattern = rf'(?<!\w){re.escape(answer)}(?!\w)'

    return len(re.findall(pattern, text))

