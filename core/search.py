from time import sleep
import re

from ddgs import DDGS
from ddgs.exceptions import DDGSException, TimeoutException
from core.matching import normalize_latex

def search(query: str, limit: int = 100, timeout: int = 20, backend: str = 'auto') -> list[dict]:
    query = normalize_latex(query)
    query = re.sub(r'</?(?:p|div|span|br|b|i|strong|em)\b[^>]*>', ' ', query, flags=re.I)
    query = ' '.join(query.split())
    for attempt in range(3):
        try:
            with DDGS(timeout=timeout) as ddgs:
                return list(
                    ddgs.text(
                        query,
                        region="ru-ru",
                        max_results=limit,
                        backend=backend,
                    )
                )
        except DDGSException as exc:
            retryable = isinstance(exc, TimeoutException) or (
                type(exc) is DDGSException and str(exc) == "No results found."
            )
            if not retryable or attempt == 2:
                raise
            sleep(1)
