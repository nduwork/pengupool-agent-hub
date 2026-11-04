---
name: macos-shipping
description: |
  Use when signing, notarizing, packaging or releasing a macOS app outside the Mac App Store: Developer ID
  certificates, hardened runtime, entitlements, notarytool credentials, stapling, DMGs, CI signing, update
  security, or a Gatekeeper warning, notary rejection or lost privacy permission. Covers Electron
  (electron-builder), SwiftPM and Xcode apps. Examples: "stop the unidentified-developer block", "why was
  notarization rejected", "set up signing in CI", "which entitlements does this app need".
triggers:
  - macos-shipping
  - notarize
  - notarization
  - developer id
  - gatekeeper
  - codesign
---

# macos-shipping

How a macOS app goes from an unsigned build to a Developer ID signed, notarized and stapled `.app`
and DMG. App-specific facts (identities, bundle IDs, past releases) are in PenguPool memory
(`pengupool search`), not here.

## The chain, in order

1. **Identity.** A *Developer ID Application* certificate, private key in the keychain. Apple
   Development and Apple Distribution certificates look usable, but notarization rejects them, and
   ad-hoc (`-s -`) signatures too.
2. **Sign inside out** with hardened runtime (`--options runtime`) and a secure timestamp
   (`--timestamp`) on every Mach-O file, then each nested bundle, then the app. Never `codesign
   --deep` to sign. `--deep` is fine to *verify*.
3. **Minimal entitlements**, explicit, on executables only (see below).
4. **Nothing writes into `Contents/` after signing.** Any change breaks the seal ("signature of the
   binary is invalid"). An ad-hoc `codesign --deep` belongs only on the no-certificate path.
5. **Sign the DMG** with `--timestamp`, by the certificate's SHA-1 hash when two share a name
   (after the `.app` is stapled, step 6).
6. **Notarize twice** (an automated scan: minutes; a new team's first can take tens of minutes):
   the `.app` (zipped), then staple the `.app`; then build, sign, notarize and staple the DMG. A
   ticket on the DMG alone fails `syspolicy_check distribution` ("Notary Ticket Missing"). Read
   each log, require `status: Accepted`; on Invalid set the artifact aside and exit non-zero.
7. **Verify** both, then `gatekeeper` the DMG: a quarantined copy, as a browser download.
8. Test a browser-downloaded copy on another Mac or user account before announcing. Expect
   macOS's one-time "downloaded from the Internet" confirmation with an Open button: notarization
   removes the unidentified-developer block, not that. Never promise users "no warning".

## The script

`scripts/macos-release.sh` (in this skill's folder) runs the chain. It reads names and paths from
the environment, never secret values.

| Command | Does |
| --- | --- |
| `preflight` | Exactly one identity matches `SIGN_ID` and it is Developer ID Application; notary credentials accepted |
| `sign <App.app> [ent] [inherit]` | Inside-out, hardened runtime, timestamps; tools and helper apps get `inherit` (none if omitted); XPC services and extensions keep their own |
| `dmg <App.app> <out.dmg>` | `ditto` staging, `/Applications` link, UDZO, `hdiutil verify`, signed |
| `notarize <file>` | Submit, wait, require Accepted, save `<file>.notary-log.json`, staple, validate; an Invalid one is renamed `.rejected` |
| `verify <App.app or .dmg>` | Read-only: strict check; Developer ID, team, runtime and timestamp on every Mach-O; staple; `spctl` |
| `gatekeeper <App.dmg>` | Quarantined copy, mounted, app copied out: `spctl -t exec` and `syspolicy_check distribution` |
| `selftest` | Ad-hoc run on a throwaway bundle; run it after changing the script |

`NOTARY_PROFILE` (default `notary`) names a notarytool keychain profile, the default on a Mac. CI
sets `ASC_KEY_PATH`, `ASC_KEY_ID`, `ASC_ISSUER` instead. `SIGN_ID` picks the identity: a SHA-1
hash from `security find-identity` is never ambiguous.

Which steps apply:
- **Electron:** electron-builder signs, notarizes and staples the `.app`; then `dmg`, `notarize`
  the DMG, `verify`, `gatekeeper`. Read [references/electron.md](references/electron.md).
- **Xcode:** export with the Developer ID method; then `notarize` the `.app`, `dmg`, `notarize`
  the DMG, `verify`, `gatekeeper`.
- **SwiftPM or a hand-assembled bundle:** `sign` first, then as Xcode. Read
  [references/native.md](references/native.md).

## Entitlements policy

- Start from none (native) or `com.apple.security.cs.allow-jit` only (Electron). Give electron-builder
  both `entitlements` and `entitlementsInherit`; bundled CLIs get the inherit file, so check both.
- Add a key only for a feature in use, with its `NS…UsageDescription`. Driving another app with
  `osascript` needs `automation.apple-events` + `NSAppleEventsUsageDescription`, or it fails
  silently with -1743.
- Never `get-task-allow`. No `allow-unsigned-executable-memory` on modern Electron.
  `disable-library-validation` only to load dylibs signed by another team.
- `network.*` and `files.*` mean nothing without App Sandbox. Spawning signed binaries needs no
  entitlement.
- `plutil -lint`, then read `codesign -d --entitlements - --xml <App>`: duplicate keys pass the lint
  but codesign rejects them.

## Verify (every release)

```sh
scripts/macos-release.sh verify "<App>.app"   # expect spctl: source=Notarized Developer ID
scripts/macos-release.sh verify "<App>.dmg"
scripts/macos-release.sh gatekeeper "<App>.dmg"   # the user's double-click, scripted
```

Expect `Authority=Developer ID Application` › `Developer ID Certification Authority` › `Apple Root
CA`, `flags=…runtime` and a `Timestamp` on the app and every bundled binary.

Then download the DMG through a browser (so it is quarantined) on a second Mac or a fresh user
account and open it. The build Mac never quarantines its own builds; `curl` downloads aren't
quarantined either.

## Release checklist

- The distribution target turns signing on by itself; local and dev builds stay ad hoc.
- Tag the release commit before building, so the artifact's version matches the tag.
- Test the signed path on the branch, locally, before merging a signing change.
- A self-updater checks the new app against the Developer ID anchor and Team ID before swapping
  ([references/packaging-and-updates.md](references/packaging-and-updates.md)).

## What only the owner does

Say these steps to the owner plainly; never do them for them or ask for secret values.
1. **Create the certificate** (Account Holder only): Xcode › Settings › Accounts › team › Manage
   Certificates › + › Developer ID Application. Greyed out means the wrong role is signed in.
2. **Store notary credentials once**, in their own Terminal: `xcrun notarytool store-credentials
   notary` with an App Store Connect API key or with `--apple-id <email> --team-id <TEAM>` and an
   app-specific password. Then the agent runs `scripts/macos-release.sh preflight`.
3. **For CI**, add the secrets in [references/credentials-and-ci.md](references/credentials-and-ci.md).

## Reference (read the one that applies)

| When | Read |
| --- | --- |
| Certificates, Team ID, notary credentials, CI secrets, temporary keychains | [references/credentials-and-ci.md](references/credentials-and-ci.md) |
| electron-builder config, entitlement files, `signIgnore`, universal builds | [references/electron.md](references/electron.md) |
| Xcode export, SwiftPM bundles, hand-signing, stable dev identity | [references/native.md](references/native.md) |
| DMG, release flow and version tags, CLI links, self-updater checks | [references/packaging-and-updates.md](references/packaging-and-updates.md) |
| A rejection, a Gatekeeper warning, a crash after signing, lost privacy grants | [references/troubleshooting.md](references/troubleshooting.md) |
| Mac App Store: sandbox, entitlement differences, hand-off | [references/mac-app-store.md](references/mac-app-store.md) |

iOS and App Store Connect work belongs to `ios-app-agent`: hand it to your parent.

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Audit before changing: run `verify` on the bundle to see where it stands.
3. Ask the owner before anything outward-facing or hard to undo: publishing a release, revoking a
   certificate, rotating a key, changing trust settings.
4. Reply with the outcome and its evidence: commands, output, the notary submission ID and what its
   log said. PenguPool records the work; write no log.
