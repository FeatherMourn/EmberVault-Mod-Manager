# EmberVault Mod Manager Roadmap

The Mod Manager is currently a read-only, Passport-driven research and review
module. It does not install, enable, disable, update, execute, or mutate mods,
saves, or live game files.

## Implemented

- Package inventory and deterministic search
- Build and client/server target compatibility review
- Dependency and SHA-256 metadata review
- Plan-only update previews
- Save Manager backup-readiness evidence review
- Troubleshooter recovery-history summaries
- Control Center approval-display payloads with approval disabled
- CI checks for tests and read-only manifest capabilities
- Control Center read-only review adapter, UI component, and smoke workflow
- Standalone QML review shell and sanitized interface snapshot model
- Snapshot-bound UI fields with structural smoke coverage; native Qt launch remains environment-dependent
- Controlled launcher with checked-in Passport fixture loading and explicit missing-Qt failure behavior
- PySide6 optional binding documented; offscreen smoke test enabled where available
- Functional query, build, and target filtering with selected Passport detail display
- Multi-record catalog loading with selectable rows and valid/partial/review-required states
- Selected-record compatibility, integrity, backup, recovery, and approval states derived dynamically
- Review-state filters, evidence/dependency/hash warnings, and plan-only update preview messaging
- Plan-only comparison details for versions, hashes, dependencies, builds, targets, evidence, and backup gates
- Supplied Save Manager backup and Troubleshooter recovery evidence bound to selected records
- Read-only evidence timeline covering provenance, source changes, integrity, compatibility, contradictions, recovery, and plan previews
- Sanitized local JSON review dossier export with public export disabled
- Local private dossier history with new/resolved/changed comparison summary

## Deferred and gated

- Richer Passport schema validation and migration fixtures
- Installation, enable/disable, update execution, and runtime hooks
- Save mutation, live-game testing, and public publication

Any deferred mutation or runtime capability requires a separate explicit
approval and must preserve provenance, hashes, recovery evidence, and audit
history.
