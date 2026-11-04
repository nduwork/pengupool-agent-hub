# Native apps: Xcode and SwiftPM

## Xcode

1. Target settings: Hardened Runtime capability on, Signing Certificate *Developer ID Application*,
   Team set, `CODE_SIGN_INJECT_BASE_ENTITLEMENTS = NO` for Release (keeps `get-task-allow` out).
2. Archive and export:

   ```sh
   xcodebuild -scheme <Scheme> -configuration Release -archivePath build/App.xcarchive archive
   xcodebuild -exportArchive -archivePath build/App.xcarchive -exportPath build/export \
     -exportOptionsPlist ExportOptions.plist
   ```

   `ExportOptions.plist`: `method` = `developer-id` (shown as "Direct Distribution" in newer
   Xcode), `signingStyle` = `manual` or `automatic`, `teamID`.
3. Then `scripts/macos-release.sh notarize App.app` (or Xcode's "Distribute App › Direct
   Distribution", which notarizes and staples the `.app`), `dmg`, `notarize App.dmg`, `verify`
   both, `gatekeeper App.dmg`.

## SwiftPM or a hand-assembled bundle

1. Build the release binary (`swift build -c release --arch arm64 --arch x86_64` for universal).
2. Assemble `App.app/Contents/{MacOS/App, Info.plist, Resources/}`; put helper tools in
   `Contents/MacOS` or `Contents/Helpers`, frameworks in `Contents/Frameworks`.
3. `scripts/macos-release.sh sign App.app [entitlements.plist]`: inside out, deepest first,
   hardened runtime, timestamps; nested executables get the inherit entitlements (none if omitted),
   libraries none, resource-only bundles and object files are skipped.
4. `notarize App.app` (zips it, submits, staples the `.app`), `dmg App.app App.dmg`,
   `notarize App.dmg`, `verify App.app`, `verify App.dmg`, `gatekeeper App.dmg`. To ship a zip
   instead: after `notarize App.app`, zip the stapled app again (`ditto -c -k --keepParent`); a
   zip can't carry a ticket itself.

XPC services, app extensions, plug-ins and login items are started by launchd or a host, not the
app, so they never get the app's inherit file. `sign` keeps the entitlements each one already
carries (Xcode builds sign them correctly). To give one its own, sign it **before** running `sign`:

```sh
codesign --force --sign "<identity or SHA-1>" --timestamp --options runtime \
  --entitlements <its.plist> App.app/Contents/XPCServices/<Name>.xpc
scripts/macos-release.sh sign App.app <app.plist> [<inherit.plist>]   # keeps those entitlements
```

Rules for hand-signing:
- Sign each item once, inside out. Never `--deep` to sign.
- Entitlements go on executables (the main app, helper apps, XPC services, standalone tools), never
  on dylibs or frameworks.
- Sign the final bundle last and touch nothing after.
- Universal binaries: check every Mach-O with `lipo -archs` before signing.

## Stable dev identity

When Developer ID can't be used locally, sign dev builds with one self-signed code-signing
certificate created once in Keychain Access (Certificate Assistant › Create a Certificate › Code
Signing). Its designated requirement survives rebuilds, so privacy grants and keychain access stop
resetting; ad-hoc signing (cdhash requirement) resets them on every build. Dev-only: it can't be
notarized.

## Sparkle (native auto-update)

Sign each update with the EdDSA key (`sign_update`), put `sparkle:edSignature` and a strictly
increasing `CFBundleVersion` in the appcast, and ship a notarized, stapled DMG or zip. Keep the
private EdDSA key in the keychain or a CI secret, never in the repository. See
[packaging-and-updates.md](packaging-and-updates.md).
