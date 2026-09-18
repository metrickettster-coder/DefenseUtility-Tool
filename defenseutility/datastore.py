import json
from functools import lru_cache
from importlib import resources
from typing import Any


def _load(filename: str) -> list[dict[str, Any]]:
    with resources.files("defenseutility.data").joinpath(filename).open("r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def load_clauses() -> list[dict[str, Any]]:
    return _load("clauses.json")


@lru_cache(maxsize=None)
def load_controls() -> list[dict[str, Any]]:
    return _load("nist_800_171_controls.json")


@lru_cache(maxsize=None)
def load_stig_checks() -> list[dict[str, Any]]:
    return _load("stig_checks.json")


@lru_cache(maxsize=None)
def load_standards() -> list[dict[str, Any]]:
    return _load("standards.json")
