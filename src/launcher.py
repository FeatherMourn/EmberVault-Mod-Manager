"""Controlled standalone launcher for the read-only Mod Manager UI."""
from __future__ import annotations

import json
from pathlib import Path


def load_fixture() -> list[dict]:
    fixture = Path(__file__).parents[1] / "tests" / "fixtures" / "passports.json"
    records = json.loads(fixture.read_text(encoding="utf-8"))
    valid = records["valid"]
    return [{"package_id": valid["id"], "version": valid["version"]}]


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
