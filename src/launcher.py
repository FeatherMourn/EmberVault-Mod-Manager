"""Controlled standalone launcher for the read-only Mod Manager UI."""
from __future__ import annotations

import json
from pathlib import Path


def load_fixture() -> list[dict]:
    fixture = Path(__file__).parents[1] / "tests" / "fixtures" / "passports.json"
    records = json.loads(fixture.read_text(encoding="utf-8"))
    output = []
    for case, passport in records.items():
        output.append({
            "package_id": passport.get("id", case), "version": passport.get("version", "unknown"),
            "builds": passport.get("builds", []), "targets": passport.get("targets", []),
            "dependencies": passport.get("dependencies", []), "files": passport.get("files", []),
            "provenance": passport.get("provenance", {}), "evidence": passport.get("evidence", []),
            "review_state": "valid" if case == "valid" else ("partial" if case == "cross_build" else "review-required"),
            "candidate_version": (passport.get("version", "unknown") + ".candidate") if case == "valid" else passport.get("version", "unknown"),
            "save_evidence": {"backup_readiness": "ready" if case == "valid" else "review-required", "rollback_readiness": "ready" if case == "valid" else "unknown"},
            "troubleshooter_history": {"report_count": 1, "recovery_state": "ready" if case == "valid" else "review-required"},
            "timeline": [
                {"kind": "provenance", "summary": "Source metadata recorded"},
                {"kind": "source-change", "summary": "Source and build scope recorded"},
                {"kind": "integrity", "summary": "SHA-256 and dependency review recorded"},
                {"kind": "compatibility", "summary": "Build and target compatibility reviewed"},
                {"kind": "evidence", "summary": "Evidence state: " + ("valid" if case == "valid" else "review-required")},
                {"kind": "contradiction", "summary": "No contradiction supplied" if case == "valid" else "Contradiction history remains review-required"},
                {"kind": "recovery", "summary": "Save Manager and Troubleshooter evidence supplied"},
                {"kind": "preview", "summary": "Update preview remains plan-only"},
            ],
        })
    return output


def main() -> int:
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtWidgets import QApplication
    except ImportError as error:
        raise SystemExit("PySide6 is required to launch the standalone UI; no dependency was installed.") from error
    app = QApplication([])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("passportFixture", load_fixture())
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "ui" / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    main()
