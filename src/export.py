"""Local-only review dossier export."""
from __future__ import annotations

import json
from pathlib import Path

from .module import build_review_dossier


def export_dossier(snapshot: dict, destination: str | Path) -> Path:
    path = Path(destination)
    if path.suffix.lower() != ".json":
        raise ValueError("Dossier export must use a .json destination.")
    if "public" in {part.casefold() for part in path.parts}:
        raise ValueError("Public dossier destinations are disabled.")
    dossier = build_review_dossier(snapshot)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dossier, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
