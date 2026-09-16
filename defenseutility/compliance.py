import re
from dataclasses import dataclass, field
from typing import Any

from .datastore import load_clauses, load_controls

DEFAULT_BASELINE = [
    "FAR 52.204-21",
    "DFARS 252.204-7012",
    "DFARS 252.204-7019",
    "DFARS 252.204-7020",
    "DFARS 252.204-7021",
    "3.1.1",
    "3.2.1",
    "3.3.1",
    "3.4.1",
    "3.5.1",
    "3.6.1",
    "3.7.1",
    "3.8.1",
    "3.9.1",
    "3.10.1",
    "3.11.1",
    "3.12.1",
    "3.13.1",
    "3.14.1",
]


@dataclass
class ComplianceReport:
    referenced: list[dict[str, Any]] = field(default_factory=list)
    missing: list[dict[str, Any]] = field(default_factory=list)

    @property
    def coverage_ratio(self) -> float:
        total = len(self.referenced) + len(self.missing)
        return len(self.referenced) / total if total else 1.0


def _normalize_id(item_id: str) -> str:
    return re.sub(r"[^a-z0-9]", "", item_id.lower())


def _is_referenced(text_normalized: str, text_lower: str, item: dict[str, Any]) -> bool:
    if _normalize_id(item["id"]) in text_normalized:
        return True
    return any(kw.lower() in text_lower for kw in item.get("keywords", []))


def _catalog() -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for clause in load_clauses():
        catalog[clause["id"]] = {**clause, "source": "clause"}
    for control in load_controls():
        catalog[control["id"]] = {**control, "source": "nist_800_171"}
    return catalog


def check_document(text: str, baseline_ids: list[str] | None = None) -> ComplianceReport:
    baseline_ids = baseline_ids if baseline_ids is not None else DEFAULT_BASELINE
    catalog = _catalog()
    text_lower = text.lower()
    text_normalized = re.sub(r"[^a-z0-9]", "", text_lower)

    report = ComplianceReport()
    for item_id in baseline_ids:
        item = catalog.get(item_id)
        if item is None:
            continue
        if _is_referenced(text_normalized, text_lower, item):
            report.referenced.append(item)
        else:
            report.missing.append(item)
    return report
