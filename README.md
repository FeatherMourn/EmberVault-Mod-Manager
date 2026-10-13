# EmberVault Mod Manager

The Mod Manager is an independently packaged, embedded EmberVault module for
Passport-driven, profile-scoped mod research and review. It inventories and
searches supplied package metadata, reviews build and client/server target
compatibility, checks declared dependencies and hashes, creates plan-only
update previews, consumes Save Manager backup evidence, summarizes
Troubleshooter recovery history, and prepares a Control Center approval view.

The first release is deliberately contract-first and read-only. All operations
return deterministic metadata or review payloads and never install, enable,
disable, update, execute, repair, or mutate saves. Runtime behavior remains
unverified. Any future package change must be separately approved and go
through Control Center's package service and operation/audit system.

## UI runtime

The optional standalone UI binding is PySide6. The launcher loads the checked-in
Passport fixture and exposes it to QML as read-only data. Environments without
PySide6 receive a clear dependency message; no dependency is installed by the
application.
Mod Manager For EmberVault
