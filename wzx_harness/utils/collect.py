"""Model discovery shared by conftest and the test module."""

from __future__ import annotations

import os
import re
from pathlib import Path

MODEL_PATTERNS = ("*.3mf", "*.stl")


def resolve_models_dirs(explicit) -> list[Path]:
    """Normalize --models-dir (append+nargs -> list of lists) and OWZX_MODELS_DIR."""
    if explicit:
        parts: list[str] = []
        for item in explicit:
            if isinstance(item, (list, tuple)):
                parts.extend(str(p) for p in item)
            else:
                parts.append(str(item))
    else:
        raw = os.environ.get("OWZX_MODELS_DIR") or ""
        parts = [p for p in raw.split(os.pathsep) if p]
    return [Path(p).expanduser().resolve() for p in parts if p]


def relative_to_any(path: Path, roots: list[Path]) -> str:
    for root in roots:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.name


def collect_models(models_dirs: list[Path], case_regex: str) -> list[dict]:
    """Scan model dirs and return [{'path': Path, 'rel': str}, ...] sorted by rel."""
    models: list[dict] = []
    seen: set[Path] = set()
    for root in models_dirs:
        for pattern in MODEL_PATTERNS:
            for path in sorted(root.rglob(pattern)):
                if path in seen:
                    continue
                seen.add(path)
                models.append(
                    {"path": path, "rel": relative_to_any(path, models_dirs)}
                )
    if case_regex:
        pattern = re.compile(case_regex)
        models = [m for m in models if pattern.search(m["rel"])]
    models.sort(key=lambda m: m["rel"])
    return models
