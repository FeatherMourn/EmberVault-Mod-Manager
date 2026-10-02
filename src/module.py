from __future__ import annotations

from embervault_sdk import ModuleContext, ModuleResult

MODULE_ID = "embervault.mod-manager"


def describe() -> dict:
    return {"id": MODULE_ID, "execution": "embedded", "application_state": "profile-scoped", "mutates_saves": False}


def inspect_package(context: ModuleContext, package: dict) -> ModuleResult:
    if context.module_id != MODULE_ID:
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(package, dict) or not package.get("id") or not package.get("version"):
        return ModuleResult("blocked", "A mod package must provide an id and version.")
    return ModuleResult("ready", "Mod package inspection completed.", {
        "package_id": str(package["id"]), "version": str(package["version"]),
        "package_type": str(package.get("package_type", "mod")),
        "application_state": "read-only",
    })


def plan_profile_change(context: ModuleContext, package_id: str, enabled: bool) -> ModuleResult:
    if context.module_id != MODULE_ID or not context.profile_id:
        return ModuleResult("blocked", "Mod Manager requires a profile-scoped context.")
    if context.capability_state not in {"plan-only", "approved"}:
        return ModuleResult("blocked", "Mod Manager requires an approved profile operation.")
    if not package_id.strip():
        return ModuleResult("blocked", "A package id is required.")
    return ModuleResult("ready", "Profile mod state change prepared.", {
        "package_id": package_id.strip(), "enabled": bool(enabled),
        "profile_id": context.profile_id, "application_state": "profile-scoped",
    })
