# Packaging, releases and updates

## DMG

- Stage with `ditto` (keeps symlinks, framework structure and signatures), add an `/Applications`
  symlink, build with `hdiutil create -srcfolder`.
- Format: UDIF. `UDZO` for the widest compatibility; `ULFO` (macOS 10.11+) and `ULMO` (10.15+) are
  smaller. Very heavily compressed images notarize slower.
- Filesystem: HFS+ works everywhere; APFS needs macOS 10.13+.
- `hdiutil verify <dmg>` before submitting.
- Sign the DMG with the **Application** identity and `--timestamp`, by its SHA-1 hash so two
  certificates with the same name can't be ambiguous (fail clearly if the hash lookup is empty).
  Never an Installer identity.
- Order, two notarizations:
  1. Sign the app (inside out), zip it (`ditto -c -k --keepParent`), `notarytool submit --wait
     --output-format json`, `stapler staple` the `.app` (electron-builder does this step itself).
  2. Build the DMG from the stapled app, sign it, submit it, `stapler staple`, `stapler validate`,
     `spctl -a -vvv -t open --context context:primary-signature <dmg>` (the disk-image form).
  3. `scripts/macos-release.sh gatekeeper <dmg>`: copy the DMG, set `com.apple.quarantine` on it as
     a browser would, mount it, `ditto` the app out, run `spctl -a -vvv -t exec` and
     `syspolicy_check distribution` (macOS 14+). A scripted stand-in for the user's double-click.
- Not Accepted: print the JSON and `notarytool log <id>`, remove or rename the DMG so a rejected
  build can't be uploaded, exit non-zero (`scripts/macos-release.sh notarize` does all three).
- **The `.app` needs its own ticket.** With only the DMG stapled, `spctl -a -t exec` still accepts
  a quarantined copy of the app, but `syspolicy_check distribution` fails with "Notary Ticket
  Missing". The DMG's notarization covers the files inside for the online check only.
- A background image and icon positions need the electron-builder `dmg` target or a `create-dmg`
  style tool; the plain `hdiutil` flow has none.
- Ship a SHA-256 next to the DMG when releasing on GitHub: `shasum -a 256 <dmg>`.

## Release flow

- The distribution target turns signing and notarization on by itself (for example `dist` sets
  `SIGN=1`): nobody has to remember a flag.
- Local installs and dev builds stay ad hoc by default, so they build on any machine. The cost: an
  ad-hoc signature's designated requirement is the cdhash, so every rebuild looks like a new app
  and privacy and keychain grants reset. Where that hurts, sign dev builds with Developer ID and
  skip notarization; a locally built app has no quarantine flag.
- **Tag the release commit before building** the DMG and installing, so the artifact's version stamp
  matches the tag. Stamp a build suffix (commit plus a digest of uncommitted changes) only on builds
  that aren't a clean checkout of the exact tag. Keep that suffix wherever version strings are
  compared (host and app, updater checks), or a dev build looks identical to the release.
- **Test the signed path on the branch**, locally and without publishing, before merging a signing
  change. Then verify a browser-downloaded copy of the real artifact.
- Show `codesign -dvv` for the app **and** each bundled CLI in the release evidence:
  `Authority=Developer ID Application`, `TeamIdentifier`, `flags=…runtime`, `Timestamp`
  (`scripts/macos-release.sh verify` checks every Mach-O).

## Bundled CLIs

A DMG drag-install creates no CLI symlinks. Link from a directory on the user's `PATH` (for
example `~/.local/bin`) into the `.app` bundle: the link keeps working, and picks up updates, as long
as the app is replaced at the same path.

## pkg installers

Only when something must install outside `/Applications` (a launch daemon, a CLI in
`/usr/local/bin`). Sign with a *Developer ID Installer* identity (`productbuild --sign`), notarize
and staple the `.pkg`. Prefer a DMG otherwise.

## Auto-update: the update must prove where it came from

| Mechanism | What it needs |
| --- | --- |
| electron-updater / Squirrel.Mac | Signed app, a `zip` target, `latest-mac.yml`; Squirrel checks the code signature itself. electron-builder 26+ can sign update manifests. |
| Sparkle | EdDSA-signed appcast items (`sparkle:edSignature`), strictly increasing `CFBundleVersion`, notarized DMG or zip. |
| Custom updater (downloads a DMG and swaps the `.app`) | Must check the new bundle itself before the swap. |

A file downloaded by the app's own HTTP code (or `curl`) has **no quarantine flag**, so Gatekeeper
never assesses it: signing alone protects nothing there.

A custom updater must anchor the check to Apple's Developer ID chain. `codesign --verify` plus a
`TeamIdentifier` string compare is **not enough**: anyone can ad-hoc sign with
`--team-identifier <TEAM>`. Before swapping:

```sh
codesign --verify --deep --strict -R='anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] exists and certificate leaf[field.1.2.840.113635.100.6.1.13] exists and certificate leaf[subject.OU] = "<TEAM>"' "$NEW" || exit 1
```

`<TEAM>` is the running app's own Team ID. Skip the check only when the running app is itself ad
hoc (a dev build), and never skip it in a release build.

Developer ID signing also keeps privacy grants across updates: the designated requirement is the
bundle identifier plus Team ID, not the cdhash. Only from one Developer ID build to the next,
though: users upgrading from an ad-hoc build get a new identity and are asked again (Automation,
local network …). Say so in the release notes.

Put `minimumSystemVersion` in the update manifest so older macOS skips an update it can't run.
