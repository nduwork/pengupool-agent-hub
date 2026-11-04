# Electron (electron-builder)

electron-builder hands signing to `@electron/osx-sign`, which walks the bundle and signs every
binary deepest first, then the `.app`, without `--deep`. With `hardenedRuntime` on it adds
`--options runtime --timestamp` to each file. Binaries copied into `Contents/Resources` (a bundled
CLI) are found and signed automatically. Do not hand-sign an Electron app; configure it.

## `build.mac` (v26 keys)

```jsonc
"mac": {
  "target": [{ "target": "dmg", "arch": ["arm64"] }],   // or "dir" and build the DMG with the script
  // "identity": null  ← remove: null disables signing. Unset = find the Developer ID in the keychain
  // "identity": "<Name (TEAMID)>"  ← to pin one: the certificate name WITHOUT "Developer ID Application: "
  "hardenedRuntime": true,
  "entitlements": "build/entitlements.mac.plist",
  "entitlementsInherit": "build/entitlements.mac.inherit.plist",
  "signIgnore": ["<non-Mach-O files that look binary, e.g. Linux builds of a CLI>"],
  "notarize": true,          // v26: a switch; credentials come from the environment
  "extendInfo": { "NS…UsageDescription": "<why, for each permission the app uses>" }
}
```

Credentials, any one set, from the environment: `APPLE_KEYCHAIN_PROFILE` (local), or
`APPLE_API_KEY` (a path to the `.p8`, not base64) + `APPLE_API_KEY_ID` + `APPLE_API_ISSUER`, or `APPLE_ID` +
`APPLE_APP_SPECIFIC_PASSWORD` + `APPLE_TEAM_ID`. `@electron/notarize` then staples the `.app`.
Keep `--publish never` unless the release step is meant to publish.

Local example: `APPLE_KEYCHAIN_PROFILE=notary npx electron-builder --mac --arm64`.

Sign the DMG yourself afterwards ([packaging-and-updates.md](packaging-and-updates.md)).

## Entitlement files: always supply both

If `build/entitlements.mac.plist` is missing, v26 gives the app **and every nested binary** its
template: `allow-jit`, `allow-unsigned-executable-memory` and `disable-library-validation`. That is
looser than needed. Modern Electron needs only `allow-jit`. Ship both files; for most apps they are
identical:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>com.apple.security.cs.allow-jit</key><true/>
  <!-- add only what a feature uses, e.g. com.apple.security.automation.apple-events -->
</dict></plist>
```

A crash on launch right after signing usually means `allow-jit` is missing.

- **Bundled CLIs and helpers get the inherit file.** A binary copied into `Contents/Resources` is
  signed with `entitlementsInherit`, not the main file. A trimmed inherit file can strip an
  entitlement the CLI needs: check what each bundled binary does before the two files differ.
- **Apple Events.** If the app or a bundled helper runs `osascript` to drive another app (Finder
  "delete" for Move to Trash, for example), add `com.apple.security.automation.apple-events` to
  both files and `NSAppleEventsUsageDescription` to `extendInfo`. Without them the hardened app
  fails silently with error -1743 and no prompt. TCC charges a child `osascript` to the responsible
  (main) app, so the main app's entitlement and purpose string are the ones that count.
- `signIgnore` non-Mach-O files that look binary (Linux ELF builds of a bundled CLI): they are
  resources, and notarization ignores them anyway.

## Build scripts

- An ad-hoc `codesign --force --deep -s -` step belongs only on the no-certificate path. On the
  signed path it replaces the Developer ID signature and breaks notarization.
- Which builds sign and notarize, and version tags: [packaging-and-updates.md](packaging-and-updates.md)
  › Release flow. For a dev build signed with Developer ID, skip notarization with
  `-c.mac.notarize=false`.
- Exclude build output (`dist/**`) from `files`, or a multi-arch build can pack the previous
  architecture's DMG into the asar.

## Universal vs arm64

Default to arm64 only for developer tools. For universal: `--universal` uses `@electron/universal`,
which merges differing Mach-O files with `lipo`. Every bundled native binary (a Go or Rust CLI) must
then be built for both architectures or merged with `lipo -create`; check with `lipo -archs`. Use
`x64ArchFiles` / `singleArchFiles` when the asar differs between architectures. Notarize each
architecture's artifact; they can run in parallel.

## Versions

- Everything here is for electron-builder **v26**, the current release. v27 is a prerelease whose
  mac signing options are expected to move (under `mac.sign`) and may change before it ships: read
  the version in `package.json` and that version's docs before writing config.
- electron-builder's own `dmg` target does not notarize the DMG and does not sign it by default
  (`dmg.sign: false`). Notarize and staple the DMG separately (`scripts/macos-release.sh notarize`).
- A retry around signing helps on flaky timestamp servers; allow `timestamp.apple.com` on CI.
