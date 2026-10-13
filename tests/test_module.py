import unittest

from embervault_sdk import ModuleContext
from src.module import inspect_package, inventory_packages, plan_profile_change


class ModManagerTests(unittest.TestCase):
    def test_inspection_is_read_only(self):
        result = inspect_package(ModuleContext("embervault.mod-manager", "default", "EV-OP-1"),
                                 {"id": "demo.mod", "version": "1.0.0"})
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.data["application_state"], "read-only")

    def test_profile_change_requires_profile(self):
        result = plan_profile_change(ModuleContext("embervault.mod-manager", None, "EV-OP-2"), "demo.mod", True)
        self.assertEqual(result.status, "blocked")

    def test_inventory_search_is_deterministic_and_read_only(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-3")
        packages = [
            {"id": "z.mod", "version": "1.0.0", "builds": ["1076226"], "targets": ["client"], "sha256": "z"},
            {"id": "a.mod", "version": "2.0.0", "builds": ["1076226"], "targets": ["dedicated-server"], "sha256": "a"},
        ]
        result = inventory_packages(context, packages, build="1076226")
        self.assertEqual(result.status, "ready")
        self.assertEqual([item["package_id"] for item in result.data["packages"]], ["a.mod", "z.mod"])
        self.assertTrue(result.data["read_only"])
        self.assertFalse(result.data["executes_installation"])

    def test_inventory_filters_query_and_target(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-4")
        result = inventory_packages(context, [
            {"id": "demo.mod", "name": "Demo", "version": "1", "targets": ["client"]},
            {"id": "other.mod", "name": "Other", "version": "1", "targets": ["dedicated-server"]},
        ], query="demo", target="client")
        self.assertEqual([item["package_id"] for item in result.data["packages"]], ["demo.mod"])

    def test_inventory_rejects_incomplete_records(self):
        result = inventory_packages(ModuleContext("embervault.mod-manager", "default", "EV-OP-5"), [{"id": "missing-version"}])
        self.assertEqual(result.status, "blocked")


if __name__ == "__main__":
    unittest.main()
