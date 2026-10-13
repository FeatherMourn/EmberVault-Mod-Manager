import json
import unittest
from pathlib import Path

from embervault_sdk import ModuleContext
from src.module import approval_display, assess_backup_readiness, assess_compatibility, build_interface_snapshot, inspect_package, inventory_packages, migrate_passport, plan_profile_change, preview_update, review_package_integrity, summarize_recovery_history, validate_passport


class ModManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.passports = json.loads((Path(__file__).parent / "fixtures" / "passports.json").read_text(encoding="utf-8"))

    def test_passport_fixtures_validate_read_only_contract(self):
        context = ModuleContext("embervault.mod-manager", "research", "EV-PASS-1")
        valid = validate_passport(context, self.passports["valid"])
        self.assertEqual(valid.data["state"], "valid")
        for name in ("incomplete", "malformed"):
            result = validate_passport(context, self.passports[name])
            self.assertEqual(result.data["state"], "review-required")
            self.assertTrue(result.data["issues"])

    def test_passport_edge_fixtures_preserve_evidence_states_and_builds(self):
        context = ModuleContext("embervault.mod-manager", "research", "EV-PASS-2")
        for name in ("contradictory", "unresolved", "cross_build"):
            result = validate_passport(context, self.passports[name])
            self.assertEqual(result.status, "ready")
            self.assertEqual(result.data["passport_version"], 1)
            self.assertTrue(result.data["read_only"])
            self.assertFalse(result.data["execution_requested"])

    def test_legacy_passport_migration_preserves_identity_and_marks_gaps(self):
        legacy = {"id": "legacy.mod", "version": "0.9", "compatibility_builds": ["old-build"], "targets": ["client"]}
        result = migrate_passport(legacy)
        self.assertTrue(result.data["migrated"])
        self.assertEqual(result.data["passport"]["id"], "legacy.mod")
        self.assertEqual(result.data["passport"]["builds"], ["old-build"])
        self.assertEqual(result.data["validation_state"], "review-required")
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

    def test_update_preview_is_plan_only_and_requires_matching_identity(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-8")
        current = {"id": "demo.mod", "version": "1.0", "sha256": "a"}
        candidate = {"id": "demo.mod", "version": "1.1", "sha256": "b"}
        result = preview_update(context, current, candidate)
        self.assertTrue(result.data["update_available"])
        self.assertTrue(result.data["plan_only"])
        self.assertFalse(result.data["executed"])
        self.assertEqual(preview_update(context, current, {"id": "other.mod", "version": "1.1"}).status, "blocked")

    def test_backup_readiness_consumes_save_manager_evidence_only(self):
        context = ModuleContext("embervault.mod-manager", "default", "EV-OP-9")
        result = assess_backup_readiness(context, {
            "source_state": "ready", "backup_state": "verified", "rollback_readiness": "ready",
        })
        self.assertEqual(result.data["backup_readiness"], "ready")
        self.assertFalse(result.data["save_operations_performed"])
        self.assertFalse(result.data["mutates_saves"])

    def test_recovery_history_is_read_only(self):
        result = summarize_recovery_history(ModuleContext("embervault.mod-manager", "default", "EV-OP-10"), [
            {"recovery_state": "ready"}, {"recovery_state": "blocked"}, {"status": "ready"},
        ])
        self.assertEqual(result.data["report_count"], 3)
        self.assertEqual(result.data["recovery_states"]["ready"], 2)
        self.assertEqual(result.data["recovery_states"]["blocked"], 1)
        self.assertFalse(result.data["repairs_performed"])

    def test_approval_display_never_grants_or_executes(self):
        result = approval_display(ModuleContext("embervault.mod-manager", "default", "EV-OP-11"),
                                  {"id": "demo.mod", "version": "1"}, "partial", "ready")
        self.assertTrue(result.data["review_required"])
        self.assertEqual(result.data["contract_version"], 1)
        self.assertEqual(result.data["package"]["package_id"], "demo.mod")
        self.assertFalse(result.data["approval_granted"])
        self.assertFalse(result.data["execution_requested"])

    def test_review_boundaries_expose_safety_fields(self):
        context = ModuleContext("embervault.mod-manager", "research", "EV-OP-12")
        inventory = inventory_packages(context, [{"id": "demo.mod", "version": "1"}])
        preview = preview_update(context, {"id": "demo.mod", "version": "1"}, {"id": "demo.mod", "version": "2"})
        for result in (inventory, preview):
            self.assertEqual(result.status, "ready")
            self.assertTrue(result.data["read_only"])
        self.assertNotIn("execute", preview.data)
        self.assertNotIn("install", inventory.data)

    def test_standalone_review_ui_is_packaged_and_has_no_mutation_controls(self):
        ui = (Path(__file__).parents[1] / "ui" / "Main.qml").read_text(encoding="utf-8")
        self.assertIn("Passport research workspace", ui)
        self.assertIn("READ-ONLY", ui)
        for forbidden in ("Install", "Enable", "Disable", "Update", "Restore"):
            self.assertNotIn("text: \"" + forbidden + "\"", ui)

    def test_interface_snapshot_is_sanitized_and_plan_only(self):
        snapshot = build_interface_snapshot(
            {"id": "demo.mod", "version": "1.0.0"},
            {"compatibility_state": "partial"},
            {"integrity_state": "review-required", "sha256": "a" * 64},
            {"backup_readiness": "ready"},
            {"report_count": 2},
        )
        self.assertEqual(snapshot["package"]["package_id"], "demo.mod")
        self.assertEqual(snapshot["backup_readiness"], "ready")
        self.assertTrue(snapshot["read_only"])
        self.assertTrue(snapshot["plan_only"])
        self.assertFalse(snapshot["approval_granted"])
        self.assertEqual(snapshot["actions"], [])

    def test_ui_binds_snapshot_review_fields_without_actions(self):
        ui = (Path(__file__).parents[1] / "ui" / "Main.qml").read_text(encoding="utf-8")
        for binding in ("packageRecords", "compatibilityState", "integrityState", "backupReadiness", "recoverySummary", "approvalGranted"):
            self.assertIn(binding, ui)
        self.assertIn("No install, enable, disable, update, or runtime actions", ui)

    def test_launcher_loads_checked_in_fixture_without_mutation(self):
        from src.launcher import load_fixture
        records = load_fixture()
        self.assertEqual(records[0]["package_id"], "demo.mod")
        self.assertIn("passportFixture", (Path(__file__).parents[1] / "ui" / "Main.qml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
