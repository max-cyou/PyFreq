from time import sleep
import re

from ddgs import DDGS
from ddgs.exceptions import DDGSException
from core.matching import normalize_latex

def search(query: str, limit: int = 100) -> list[dict]:
    query = normalize_latex(query)
    query = re.sub(r'</?(?:p|div|span|br|b|i|strong|em)\b[^>]*>', ' ', query, flags=re.I)
    query = ' '.join(query.split())
    for attempt in range(3):
        try:
            with DDGS(timeout=20) as ddgs:
                return list(
                    ddgs.text(
                        query,
                        region="ru-ru",
                        max_results=limit,
                        backend="auto",
                    )
                )
        except DDGSException as exc:
            if type(exc) is not DDGSException or str(exc) != "No results found." or attempt == 2:
                raise
            sleep(1)
