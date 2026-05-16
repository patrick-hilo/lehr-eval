from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    key: str
    text: str


@dataclass(frozen=True)
class Questionnaire:
    kind: str
    version: str
    items: tuple[Item, ...]


_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
_NUMBERED_ITEM = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")


def load_questionnaire_from_markdown(path: str | Path, *, kind: str) -> Questionnaire:
    text = Path(path).read_text(encoding="utf-8")
    version = _extract_version(text, fallback=f"{kind}-v1")
    items_texts = _extract_items(text)
    if len(items_texts) != 10:
        raise ValueError(
            f"questionnaire at {path} must define exactly 10 items, found {len(items_texts)}"
        )
    items = tuple(
        Item(key=f"Item {index + 1}", text=item_text)
        for index, item_text in enumerate(items_texts)
    )
    return Questionnaire(kind=kind, version=version, items=items)


def _extract_version(text: str, *, fallback: str) -> str:
    in_version = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("## version"):
            in_version = True
            continue
        if in_version:
            if line.startswith("#"):
                break
            if line:
                return line
    return fallback


def _extract_items(text: str) -> list[str]:
    items: list[str] = []
    in_items = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.lower().startswith("## items"):
            in_items = True
            continue
        if not in_items:
            continue
        if stripped.startswith("## "):
            break
        match = _NUMBERED_ITEM.match(line)
        if match is None:
            continue
        items.append(match.group(2))
    return items


def _default_questionnaire(kind: str, version: str) -> Questionnaire:
    items = tuple(Item(key=f"Item {n}", text=f"Item {n}") for n in range(1, 11))
    return Questionnaire(kind=kind, version=version, items=items)


def _load_default(kind: str, filename: str) -> Questionnaire:
    path = _EXAMPLES_DIR / filename
    if path.exists():
        try:
            return load_questionnaire_from_markdown(path, kind=kind)
        except (OSError, ValueError):
            pass
    return _default_questionnaire(kind, version=f"{kind}-v1")


_LOWER_QUESTIONNAIRE = _load_default("unterstufe", "fragebogen-unterstufe.md")
_UPPER_QUESTIONNAIRE = _load_default("oberstufe", "fragebogen-oberstufe.md")


def questionnaire_for_grade(grade: int) -> Questionnaire:
    if 1 <= grade <= 6:
        return _LOWER_QUESTIONNAIRE
    if 7 <= grade <= 10:
        return _UPPER_QUESTIONNAIRE
    raise ValueError("grade must be between 1 and 10")
