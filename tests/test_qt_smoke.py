import os
import unittest
from pathlib import Path


class QtSmokeTests(unittest.TestCase):
    @unittest.skipUnless(__import__("importlib").util.find_spec("PySide6"), "PySide6 is not installed")
    def test_qml_shell_loads_offscreen_with_fixture(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtCore import QTimer, QUrl
        from PySide6.QtQml import QQmlApplicationEngine
        from PySide6.QtWidgets import QApplication
        from src.launcher import load_fixture

        app = QApplication.instance() or QApplication([])
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("passportFixture", load_fixture())
        engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "ui" / "Main.qml")))
        self.assertTrue(engine.rootObjects())
        QTimer.singleShot(0, app.quit)
        app.exec()
        self.assertEqual(len(load_fixture()), 1)


if __name__ == "__main__":
    unittest.main()
