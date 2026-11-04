# Troubleshooting

Read the notary log first: `xcrun notarytool log <submission-id> --keychain-profile notary
log.json` (the script saves it as `<file>.notary-log.json`). It names the file and the problem.

## Notary rejections

| Message | Cause → fix |
| --- | --- |
| The binary is not signed with a valid Developer ID certificate. | Signed with Apple Development, Apple Distribution or ad-hoc → sign with Developer ID Application |
| The signature does not include a secure timestamp. | Missing `--timestamp`, or `timestamp.apple.com` unreachable from CI → add it; allow the host |
| The executable does not have the hardened runtime enabled. | `hardenedRuntime: false`, or a binary signed outside the main flow without `--options runtime` |
| The signature of the binary is invalid. | The bundle changed after signing: a later ad-hoc re-sign, or a write into `Contents/` → remove the step |
| The executable requests the com.apple.security.get-task-allow entitlement. | Debug entitlement in a release build → remove it (Xcode: `CODE_SIGN_INJECT_BASE_ENTITLEMENTS = NO`) |
| Embedded entitlements are invalid / app aborts at launch | Malformed plist or duplicate keys → `plutil -lint`, then read `codesign -d --entitlements - --xml` |
| The binary uses an SDK older than the 10.9 SDK. | A very old prebuilt binary → rebuild it or drop it |
| `notarytool` 401 Unauthenticated | Stale or revoked key, or a missing profile → `notarytool history`; retry with `--no-s3-acceleration` |

## Gatekeeper and launch

Work through these on the shipped artifact, read-only (no `--sign`, no `--force`):

1. `spctl -a -vvv -t exec <App>`: the `source=` line should say `Notarized Developer ID`.
2. `xcrun stapler validate <App>` and `<dmg>`.
3. `codesign --verify --deep --strict --verbose=2 <App>`.
4. `xattr -p com.apple.quarantine <App>`: present only on downloaded copies.
5. `log show --last 5m --predicate 'subsystem == "com.apple.syspolicy" OR process == "amfid"'` for
   the denial reason.
6. "Apple cannot check it for malicious software": not notarized, or offline and not stapled.
7. "different Team IDs" at launch: a nested binary is signed by another identity or ad-hoc;
   `scripts/macos-release.sh verify` names it.
8. Crash right after signing: missing `allow-jit` (Electron) or an entitlement a feature needs.
9. A feature that drives another app silently does nothing, error -1743: Apple Events entitlement
   or `NSAppleEventsUsageDescription` missing (see Privacy permissions below).
10. Works on the build Mac, blocked elsewhere: the build Mac never quarantines its own builds.
    `scripts/macos-release.sh gatekeeper <dmg>` reproduces a download.
11. `syspolicy_check distribution` says "Notary Ticket Missing" while `spctl` accepts: only the DMG
    was stapled. Notarize and staple the `.app` too, then rebuild the DMG.
12. Expected chain on every binary (`codesign -dvv`): `Authority=Developer ID Application`, then
    `Developer ID Certification Authority`, then `Apple Root CA`. Anything else (Apple Development,
    "adhoc", no Authority) can't be notarized.

## Gatekeeper facts for users

- A notarized app opened from a downloaded DMG still shows the one-time "… is an app downloaded
  from the Internet. Are you sure you want to open it?" confirmation, with an Open button. That is
  expected. Notarization removes the unidentified-developer block, and with it the need for Open
  Anyway or `xattr`. User-facing docs must not claim "no warning".
- A browser download gets `com.apple.quarantine`; a `curl` download doesn't. That is why `curl | sh`
  installers skip Gatekeeper, and also why they need the user's trust.
- Since macOS 15, Control-click › Open no longer bypasses Gatekeeper. An unsigned or unnotarized app
  needs System Settings › Privacy & Security › Open Anyway, or `xattr -dr com.apple.quarantine
  <App>`. Notarization is the only real fix; give users the workaround only for dev builds.

Keychain errors (`errSecInternalComponent`, "Invalid trust settings"): inspect first
(`security find-identity -v -p codesigning`, the certificate's trust in Keychain Access). A locked
keychain or a missing intermediate certificate is common. Never change trust settings without the
owner's go-ahead.

## Privacy permissions (TCC)

- Grants follow the designated requirement. Ad-hoc → cdhash → every build is a new app and grants
  reset or silently fail (EPERM, no prompt). Developer ID → identifier + Team ID → grants survive.
- The first Developer ID release after ad-hoc builds is a new code identity: users are asked again
  for Automation, local network and every other grant. Say so in the release notes.
- Every permission needs its purpose string in `Info.plist`: `NSLocalNetworkUsageDescription`,
  `NSAppleEventsUsageDescription`, camera, microphone. A missing string means a crash or a silent
  denial.
- Apple Events (-1743, no prompt): the entitlement and purpose string are missing on the main app;
  details in [electron.md](electron.md) › Entitlement files. A framework call (Electron
  `shell.trashItem`, `NSWorkspace`) avoids Apple Events entirely.
- Reset to test the prompt again: `tccutil reset <Service> <bundle-id>`.
- Full Disk Access can't be requested in code; guide the user to System Settings.
