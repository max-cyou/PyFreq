from time import sleep

from ddgs import DDGS
from ddgs.exceptions import DDGSException

def search(query: str, limit: int = 100) -> list[dict]:
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
