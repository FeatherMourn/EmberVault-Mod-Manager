from __future__ import annotations

from embervault_sdk import ModuleContext, ModuleResult

MODULE_ID = "embervault.mod-manager"


def _valid_context(context: ModuleContext) -> bool:
    return isinstance(context, ModuleContext) and context.module_id == MODULE_ID


def _text(value: object) -> str:
    return str(value or "").strip()


def _values(package: dict, key: str) -> list[str]:
    value = package.get(key, [])
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return sorted({_text(item) for item in value if _text(item)})


def inventory_packages(
    context: ModuleContext,
    packages: list[dict],
    query: str = "",
    build: str = "",
    target: str = "",
) -> ModuleResult:
    """Search supplied package metadata without touching the filesystem or runtime."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(packages, list):
        return ModuleResult("blocked", "Package inventory must be a list of metadata records.")

    records = []
    for package in packages:
        if not isinstance(package, dict) or not _text(package.get("id")) or not _text(package.get("version")):
            return ModuleResult("blocked", "Every package record must provide an id and version.")
        builds = _values(package, "builds") or _values(package, "compatibility_builds")
        targets = _values(package, "targets") or _values(package, "compatibility_targets")
        searchable = " ".join([
            _text(package.get("id")), _text(package.get("name")), _text(package.get("version")),
            " ".join(builds), " ".join(targets), " ".join(_values(package, "dependencies")),
        ]).casefold()
        if query.strip().casefold() not in searchable:
            continue
        if build.strip() and build.strip() not in builds:
            continue
        if target.strip() and target.strip() not in targets:
            continue
        records.append({
            "package_id": _text(package["id"]),
            "name": _text(package.get("name")),
            "version": _text(package["version"]),
            "builds": builds,
            "targets": targets,
            "dependencies": _values(package, "dependencies"),
            "sha256": _text(package.get("sha256")),
            "provenance": package.get("provenance", {}),
            "compatibility_state": _text(package.get("compatibility_state", "unknown")),
        })

    records.sort(key=lambda item: (item["package_id"].casefold(), item["version"], item["sha256"]))
    return ModuleResult("ready", "Package inventory search completed.", {
        "packages": records,
        "count": len(records),
        "read_only": True,
        "mutates_workspace": False,
        "executes_installation": False,
        "runtime_approval": False,
    })


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
