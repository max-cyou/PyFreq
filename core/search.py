
from ddgs import DDGS

def search(query: str, limit: int = 100) -> list[dict]:
    with DDGS(timeout=20) as ddgs:
        return list(
            ddgs.text(
                query,
                region="ru-ru",
                max_results=limit,
                backend="google",
            )
        )
