"""Local sanitized Passport dossier history and comparison."""
from __future__ import annotations

import json
from pathlib import Path


def compare_dossiers(previous: dict, current: dict) -> dict:
    if not isinstance(previous, dict) or not isinstance(current, dict):
        raise ValueError("Dossier comparison requires two objects.")
    fields = ("compatibility", "integrity", "backup_readiness", "recovery_history", "timeline")
    changed = {field: {"previous": previous.get(field), "current": current.get(field)}
               for field in fields if previous.get(field) != current.get(field)}
    previous_events = {json.dumps(item, sort_keys=True) for item in previous.get("timeline", [])}
    current_events = {json.dumps(item, sort_keys=True) for item in current.get("timeline", [])}
    return {
        "comparison_version": 1,
        "package_id": current.get("package", {}).get("package_id", "unknown"),
        "new_evidence": sorted(current_events - previous_events),
        "resolved_evidence": sorted(previous_events - current_events),
        "changed_fields": changed,
        "read_only": True,
        "actions": [],
    }


class LocalDossierHistory:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, dossier: dict) -> None:
        if dossier.get("public") is True or dossier.get("approval_granted") is True:
            raise ValueError("Only private, unapproved dossiers may be stored.")
        history = self.read()
        history.append(dict(dossier))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("Dossier history must be a JSON list.")
        return value
