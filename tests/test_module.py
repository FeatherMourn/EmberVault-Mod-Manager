import unittest

from embervault_sdk import ModuleContext
from src.module import assess_compatibility, inspect_package, inventory_packages, plan_profile_change, review_package_integrity


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

    def test_compatibility_distinguishes_verified_partial_and_unknown(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-6")
        package = {"id": "demo.mod", "version": "1", "builds": ["1076226"], "targets": ["client"]}
        verified = assess_compatibility(context, package, "1076226", "client")
        partial = assess_compatibility(context, package, "1076226", "dedicated-server")
        unknown = assess_compatibility(context, {"id": "unknown.mod", "version": "1"}, "1076226", "client")
        self.assertEqual(verified.data["compatibility_state"], "verified")
        self.assertEqual(partial.data["compatibility_state"], "partial")
        self.assertEqual(unknown.data["compatibility_state"], "unknown")
        self.assertEqual(verified.data["runtime_behavior"], "unverified")

    def test_integrity_review_validates_hash_and_dependencies_without_file_reads(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-7")
        digest = "a" * 64
        result = review_package_integrity(context, {
            "id": "demo.mod", "version": "1", "sha256": digest,
            "dependencies": ["base.mod", "missing.mod"],
        }, [{"id": "base.mod", "version": "1"}])
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.data["hash_state"], "valid")
        self.assertEqual(result.data["resolved_dependencies"], ["base.mod"])
        self.assertEqual(result.data["unresolved_dependencies"], ["missing.mod"])
        self.assertEqual(result.data["integrity_state"], "review-required")
        self.assertFalse(result.data["reads_package_files"])


if __name__ == "__main__":
    unittest.main()
