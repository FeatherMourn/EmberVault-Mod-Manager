from __future__ import annotations

import re

from embervault_sdk import ModuleContext, ModuleResult

MODULE_ID = "embervault.mod-manager"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
_PASSPORT_FIELDS = ("id", "version", "builds", "targets", "files", "dependencies", "evidence", "provenance")


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


def validate_passport(context: ModuleContext, passport: dict) -> ModuleResult:
    """Validate a version-one Passport without reading package files or runtime state."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(passport, dict):
        return ModuleResult("blocked", "Passport must be a metadata object.")
    if passport.get("passport_version") != 1:
        return ModuleResult("blocked", "Only Passport version 1 is supported.")
    issues = [f"missing:{field}" for field in _PASSPORT_FIELDS if field not in passport]
    if passport.get("read_only") is not True:
        issues.append("read_only must be true")
    if passport.get("runtime_approval") is not False:
        issues.append("runtime_approval must be false")
    if not isinstance(passport.get("builds"), list) or not passport.get("builds"):
        issues.append("builds must be a non-empty list")
    if not isinstance(passport.get("targets"), list) or not passport.get("targets"):
        issues.append("targets must be a non-empty list")
    files = passport.get("files", [])
    if not isinstance(files, list):
        issues.append("files must be a list")
    else:
        for index, item in enumerate(files):
            if not isinstance(item, dict) or not _text(item.get("path")):
                issues.append(f"file[{index}] missing path")
            elif not _SHA256.fullmatch(_text(item.get("sha256"))):
                issues.append(f"file[{index}] invalid sha256")
    for field in ("dependencies", "evidence"):
        if not isinstance(passport.get(field), list):
            issues.append(f"{field} must be a list")
    if not isinstance(passport.get("provenance"), dict) or not passport.get("provenance"):
        issues.append("provenance must be a non-empty object")
    state = "valid" if not issues else "review-required"
    return ModuleResult("ready", "Passport validation completed.", {
        "passport_version": 1,
        "package_id": _text(passport.get("id")) or "unknown",
        "state": state,
        "issues": issues,
        "read_only": True,
        "runtime_behavior": "unverified",
        "execution_requested": False,
    })


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


def assess_compatibility(
    context: ModuleContext,
    package: dict,
    build: str,
    target: str,
) -> ModuleResult:
    """Compare supplied Passport metadata with a requested build and target."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(package, dict) or not _text(package.get("id")) or not _text(package.get("version")):
        return ModuleResult("blocked", "A package record must provide an id and version.")
    builds = _values(package, "builds") or _values(package, "compatibility_builds")
    targets = _values(package, "targets") or _values(package, "compatibility_targets")
    build_known = bool(build.strip()) and build.strip() in builds
    target_known = bool(target.strip()) and target.strip() in targets
    if build_known and target_known:
        state = "verified"
    elif build_known or target_known:
        state = "partial"
    elif builds or targets:
        state = "blocked"
    else:
        state = "unknown"
    return ModuleResult("ready", "Package compatibility assessed from supplied metadata.", {
        "package_id": _text(package["id"]),
        "version": _text(package["version"]),
        "requested_build": build.strip(),
        "requested_target": target.strip(),
        "compatibility_state": state,
        "known_builds": builds,
        "known_targets": targets,
        "runtime_behavior": "unverified",
        "read_only": True,
        "mutates_workspace": False,
    })


def review_package_integrity(
    context: ModuleContext,
    package: dict,
    dependency_catalog: list[dict] | None = None,
) -> ModuleResult:
    """Review supplied dependency declarations and hashes without opening package files."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(package, dict) or not _text(package.get("id")) or not _text(package.get("version")):
        return ModuleResult("blocked", "A package record must provide an id and version.")
    known = {
        (_text(item.get("id")), _text(item.get("version")))
        for item in (dependency_catalog or [])
        if isinstance(item, dict) and _text(item.get("id")) and _text(item.get("version"))
    }
    dependencies = _values(package, "dependencies")
    resolved = sorted(item for item in dependencies if any(identity == item for identity, _ in known))
    unresolved = sorted(item for item in dependencies if item not in resolved)
    digest = _text(package.get("sha256"))
    hash_state = "valid" if _SHA256.fullmatch(digest) else ("missing" if not digest else "invalid")
    state = "verified" if hash_state == "valid" and not unresolved else "review-required"
    return ModuleResult("ready", "Package dependency and hash review completed.", {
        "package_id": _text(package["id"]),
        "version": _text(package["version"]),
        "hash_state": hash_state,
        "sha256": digest,
        "dependencies": dependencies,
        "resolved_dependencies": resolved,
        "unresolved_dependencies": unresolved,
        "integrity_state": state,
        "read_only": True,
        "mutates_workspace": False,
        "reads_package_files": False,
    })


def preview_update(context: ModuleContext, current: dict, candidate: dict) -> ModuleResult:
    """Create a deterministic, non-executable update preview from two metadata records."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(current, dict) or not isinstance(candidate, dict):
        return ModuleResult("blocked", "Update preview requires current and candidate metadata.")
    if _text(current.get("id")) != _text(candidate.get("id")):
        return ModuleResult("blocked", "Current and candidate package ids must match.")
    changed = {
        key: {"current": current.get(key), "candidate": candidate.get(key)}
        for key in ("version", "sha256", "builds", "targets", "dependencies")
        if current.get(key) != candidate.get(key)
    }
    return ModuleResult("ready", "Plan-only update preview created.", {
        "package_id": _text(current.get("id")),
        "current_version": _text(current.get("version")),
        "candidate_version": _text(candidate.get("version")),
        "changed_fields": changed,
        "update_available": bool(changed),
        "plan_only": True,
        "executed": False,
        "installed": False,
        "read_only": True,
        "mutates_workspace": False,
    })


def assess_backup_readiness(context: ModuleContext, save_evidence: dict) -> ModuleResult:
    """Consume Save Manager evidence without opening, copying, or changing saves."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(save_evidence, dict):
        return ModuleResult("blocked", "Save Manager evidence must be a metadata record.")
    source = _text(save_evidence.get("source_state", save_evidence.get("status")))
    backup = _text(save_evidence.get("backup_state"))
    recovery = _text(save_evidence.get("rollback_readiness"))
    if source == "ready" and backup in {"ready", "verified"} and recovery in {"ready", "verified"}:
        state = "ready"
    elif source in {"blocked", "unsupported"} or backup in {"blocked", "unsupported"}:
        state = "blocked"
    else:
        state = "review-required"
    return ModuleResult("ready", "Save Manager backup readiness reviewed.", {
        "backup_readiness": state,
        "source_state": source or "unknown",
        "backup_state": backup or "unknown",
        "rollback_readiness": recovery or "unknown",
        "save_operations_performed": False,
        "read_only": True,
        "mutates_saves": False,
    })


def summarize_recovery_history(context: ModuleContext, reports: list[dict]) -> ModuleResult:
    """Summarize supplied Troubleshooter reports without repair or recovery actions."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(reports, list):
        return ModuleResult("blocked", "Troubleshooter history must be a list of reports.")
    summary = {"ready": 0, "review-required": 0, "blocked": 0, "unsupported": 0, "unknown": 0}
    for report in reports:
        if not isinstance(report, dict):
            return ModuleResult("blocked", "Every Troubleshooter report must be metadata.")
        state = _text(report.get("recovery_state", report.get("status"))) or "unknown"
        summary[state] = summary.get(state, 0) + 1
    return ModuleResult("ready", "Troubleshooter recovery history summarized.", {
        "report_count": len(reports),
        "recovery_states": summary,
        "repairs_performed": False,
        "read_only": True,
        "mutates_saves": False,
    })


def approval_display(context: ModuleContext, package: dict, compatibility_state: str, backup_readiness: str) -> ModuleResult:
    """Prepare a Control Center review payload; this never grants approval."""
    if not _valid_context(context):
        return ModuleResult("blocked", "Mod Manager received an invalid module context.")
    if not isinstance(package, dict) or not _text(package.get("id")):
        return ModuleResult("blocked", "Approval display requires a package identity.")
    gates = {
        "compatibility": compatibility_state,
        "backup_readiness": backup_readiness,
    }
    review_required = any(value != "verified" and value != "ready" for value in gates.values())
    return ModuleResult("ready", "Control Center approval display prepared.", {
        "contract_version": 1,
        "package": {"package_id": _text(package.get("id")), "version": _text(package.get("version"))},
        "package_id": _text(package.get("id")),
        "version": _text(package.get("version")),
        "gates": gates,
        "review_required": review_required,
        "approval_granted": False,
        "execution_requested": False,
        "read_only": True,
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
    """Legacy mutation entry point retained only as an explicit safety boundary."""
    return ModuleResult("blocked", "Profile mod changes are disabled in the read-only Mod Manager.", {
        "read_only": True,
        "execution_requested": False,
        "mutates_workspace": False,
    })
