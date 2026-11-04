# Mac App Store (short reference)

This helper ships outside the store. Use this page to judge whether an app could go to the Mac App
Store and to hand the work off; do not build a submission flow from it.

## What changes

| | Developer ID (outside the store) | Mac App Store |
| --- | --- | --- |
| Certificate | Developer ID Application | Apple Distribution, plus Mac Installer Distribution for the `.pkg` |
| Notarization | Required | Not used: App Review covers it |
| Package | DMG, zip or pkg | `.pkg` uploaded to App Store Connect |
| Provisioning profile | Only for restricted capabilities | Mac App Store profile, embedded as `Contents/embedded.provisionprofile` |
| App Sandbox | Optional | **Required** (`com.apple.security.app-sandbox`) |
| Updates | Your own (Sparkle, electron-updater, custom) | The store only; remove any self-updater |

## Sandbox consequences

- File access only through user choice (open and save panels) and security-scoped bookmarks;
  `files.user-selected.read-write`, `files.downloads.read-write`.
- Network needs `network.client` / `network.server` (meaningless outside the sandbox).
- Spawning arbitrary tools (git, ssh, a shell) is effectively blocked: a child inherits the sandbox
  and can't reach the user's files or dotfiles. Developer tools that drive other programs usually
  can't ship in the store.
- Apple Events need `com.apple.security.temporary-exception.apple-events` or
  `scripting-targets`, which review questions closely.
- Every helper and bundled binary must be signed with `com.apple.security.app-sandbox` and
  `com.apple.security.inherit`.
- Electron: build the `mas` target with its own entitlement files and profile.

## Hand-off

Send your parent a short brief: the app, why the store is wanted, which sandbox blockers you found
(file access, spawned tools, Apple Events, a self-updater), and the entitlements it would need. The
App Store Connect record, review and submission go to `ios-app-agent`, which owns App Store Connect
work.
