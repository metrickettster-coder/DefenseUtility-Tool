from dataclasses import dataclass
from typing import Any

from .datastore import load_clauses, load_controls


@dataclass
class SearchResult:
    source: str
    id: str
    title: str
    summary: str
    score: int


def _score(query: str, item: dict[str, Any], summary_key: str) -> int:
    q = query.lower()
    score = 0
    if q in item["id"].lower():
        score += 5
    if q in item["title"].lower():
        score += 3
    if any(q in kw.lower() for kw in item.get("keywords", [])):
        score += 2
    if q in item.get(summary_key, "").lower():
        score += 1
    return score


def search(query: str, sources: tuple[str, ...] = ("clauses", "controls")) -> list[SearchResult]:
    results: list[SearchResult] = []
    if "clauses" in sources:
        for clause in load_clauses():
            score = _score(query, clause, "summary")
            if score > 0:
                results.append(SearchResult("clause", clause["id"], clause["title"], clause["summary"], score))
    if "controls" in sources:
        for control in load_controls():
            score = _score(query, control, "summary")
            if score > 0:
                results.append(
                    SearchResult(
                        "nist_800_171",
                        control["id"],
                        f"{control['title']} ({control['family']})",
                        control["summary"],
                        score,
                    )
                )
    results.sort(key=lambda r: r.score, reverse=True)
    return results
