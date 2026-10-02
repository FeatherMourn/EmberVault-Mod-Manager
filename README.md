# EmberVault Mod Manager

The Mod Manager is an independently packaged, embedded EmberVault module for
profile-scoped mod inspection and state planning. Control Center remains the
authority that performs installation, enablement, deployment, and recovery.

The first release is deliberately contract-first: module operations return
validated plans and never mutate saves. Actual package changes must go through
Control Center's package service and operation/audit system.
Mod Manager For EmberVault
