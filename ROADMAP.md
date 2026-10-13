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

## Deferred and gated

- Richer Passport schema validation and migration fixtures
- Installation, enable/disable, update execution, and runtime hooks
- Save mutation, live-game testing, and public publication

Any deferred mutation or runtime capability requires a separate explicit
approval and must preserve provenance, hashes, recovery evidence, and audit
history.
