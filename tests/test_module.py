import unittest

from embervault_sdk import ModuleContext
from src.module import inspect_package, plan_profile_change


class ModManagerTests(unittest.TestCase):
    def test_inspection_is_read_only(self):
        result = inspect_package(ModuleContext("embervault.mod-manager", "default", "EV-OP-1"),
                                 {"id": "demo.mod", "version": "1.0.0"})
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.data["application_state"], "read-only")

    def test_profile_change_requires_profile(self):
        result = plan_profile_change(ModuleContext("embervault.mod-manager", None, "EV-OP-2"), "demo.mod", True)
        self.assertEqual(result.status, "blocked")


if __name__ == "__main__":
    unittest.main()
