---
name: ios-shipping
description: |
  Use when setting up a new iOS app for TestFlight/App Store, wiring its signing and CI, handling App Store
  Connect keys, certificates, provisioning profiles or GitHub secrets, uploading a TestFlight build, or
  preparing and unblocking an App Store submission. Examples: "set up TestFlight for this app", "rotate the
  ASC key", "why won't Add for Review work", "swap the build on 1.0", "upload a build".
triggers:
  - ios-shipping
  - testflight
  - app store connect
  - signing
---

# ios-shipping

How a SwiftUI app goes from a repo to the App Store, and how its secrets are kept. App-specific facts
(IDs, past releases) are in PenguPool memory (`pengupool search`), not here.

## Secrets: where each one lives

Master copies are in the owner's **password manager**, shared across apps. Everything else is a copy.

| Secret | Scope | Copies |
| --- | --- | --- |
| App Store Connect API key (`AuthKey_<KEYID>.p8`), key ID, issuer ID | Team, all apps | `~/.appstoreconnect/private_keys/` (chmod 600) on the Mac; GitHub secrets `ASC_KEY_P8` (base64), `ASC_KEY_ID`, `ASC_ISSUER_ID` |
| Distribution certificate `.p12` and its password | Team, all apps | GitHub secrets `IOS_CERT_P12` (base64), `IOS_CERT_PASSWORD` |
| App Store provisioning profile | **Per app** (bundle ID) | GitHub secret `IOS_PROVISIONING_PROFILE` (base64) |
| Team ID | Team | GitHub secret `FASTLANE_TEAM_ID` |
| Runner keychain password | The build Mac | GitHub secret `KEYCHAIN_PASSWORD` |
| Deploy key for the shared signing action | Per consuming repo | GitHub secret `<SIGNING_ACTION_DEPLOY_KEY>` (read-only on `<owner>/<signing-action-repo>`) |

Rules:
- **Never print, paste or commit a key's contents.** Refer to it by path or secret name only. Do not `cat` a
  `.p8`/`.p12`, do not echo secrets in workflows, do not put them in prompts or logs.
- A new app needs only a new **provisioning profile** and its GitHub secrets; reuse the team-level key and
  cert. Rotating the team key or cert means updating every app repo's secrets.
- Base64 for GitHub: `base64 -i <file> | gh secret set NAME`. The workflow decodes into `$RUNNER_TEMP`,
  never into the repo.
- When the owner sends a key file it is usually in `~/Downloads`, which the agent sandbox may not see. Ask
  them to move it themselves: `! mkdir -p ~/.appstoreconnect/private_keys && mv ~/Downloads/AuthKey_*.p8
  ~/.appstoreconnect/private_keys/ && chmod 600 ~/.appstoreconnect/private_keys/AuthKey_*.p8`.

## Setting up a new app

1. **Project as code.** XcodeGen `project.yml` is the source of truth; `Info.plist` keys (usage strings,
   `UIBackgroundModes`, `BGTaskSchedulerPermittedIdentifiers`) are mirrored there. Run `xcodegen generate`
   after any change.
2. **fastlane** (`ios/fastlane/Fastfile`) lanes: `next_build_number` (highest TestFlight build + 1 via the
   API key), `build` (gym, `export_method: app-store`), `upload` (pilot, `changelog` read from a committed
   `TestFlightNotes.txt`), `release` (build + upload). Pin gems in `Gemfile.lock`.
3. **CI workflow** `testflight.yml`: `workflow_dispatch` with `dry_run` (default true) and optional
   `build_number`; runs on the self-hosted Mac (`[self-hosted, macOS, ARM64]`). It checks out
   `<owner>/<signing-action-repo>@v1` with the deploy key and runs the build inside it. That action holds
   the keychain lock for the whole build and restores the runner keychain afterwards, so app builds sharing
   the Mac don't clobber each other. Before building it stamps `CURRENT_PROJECT_VERSION` in `project.yml`.
4. **App Store Connect record**: bundle ID, app record, manual App Store profile, a public privacy policy
   URL (if the code repo is private, host the policy on a public site), support URL, age rating, category,
   price.
5. Run once with `dry_run=true`; then `dry_run=false` uploads exactly one build.

## Shipping a build

1. Tests green locally and in CI on the commit you will ship; ship from `main` once PRs are merged.
2. Update `TestFlightNotes.txt` ("What to Test") for anything a tester should look at.
3. `gh workflow run testflight.yml --ref main -f dry_run=false`, then `gh run watch <id> --exit-status`.
4. Poll `GET /v1/builds` for a version **greater than the previous one** (don't take the latest: a fresh
   upload can take 20+ minutes to appear) until it is `VALID`. Then attach it to the App Store version.
5. **Give it to Internal Testers (every upload).** `GET /v1/apps/{app}/betaGroups` and pick the group with
   `isInternalGroup=true`. If its `hasAccessToAllBuilds` is false, no internal tester gets the build until it's
   added, and the API can't flip that flag (PATCH returns 409 `ENTITY_ERROR.ATTRIBUTE.NOT_ALLOWED`). Either the
   owner ticks "Automatically distribute" once in ASC, or add each build:
   `POST /v1/betaGroups/{groupId}/relationships/builds` `{"data":[{"type":"builds","id":"<buildId>"}]}`, once
   it's `VALID`. Set export compliance (`usesNonExemptEncryption`) or the build stays "Missing Compliance".

## Reference (read the one that applies)

| When | Read |
| --- | --- |
| Calling App Store Connect directly: builds, versions, review details, screenshots, bundle IDs, devices, IAP metadata | [references/asc-api.md](references/asc-api.md) |
| XcodeGen, signing, extension targets, betas, backend keys, CI verification, Swift 6 concurrency | [references/project-and-ci.md](references/project-and-ci.md) |
| Sign in with Apple, StoreKit, credit packs, the first paid IAP, demo mode for App Review | [references/purchases-and-review.md](references/purchases-and-review.md) |
| SwiftData + CloudKit: optional relationships, two environments, `_ckAsset` fields, CKError 2, cktool, device logs | [references/cloudkit-sync.md](references/cloudkit-sync.md) |
| Add for Review blocked, swapping a build in review, review notes, screenshots, background refresh; a 1.0 release example | [references/submission.md](references/submission.md) |
| fastlane/bundler, `.app` names, devicectl, Xcode licence, disk full, the shared runner | [references/local-tooling.md](references/local-tooling.md) |

Hard rules from those files, so they hold even unread:
- **Not possible by API:** the App Privacy questionnaire, and pressing Add for Review / Submit for Review.
  Those are the owner's clicks.
- No provider keys in Release builds; the backend URL is a build setting.
- Verification asserts against Apple's API and exits non-zero; upload is not distribution.
- CloudKit: only additive model changes; Production fields are permanent; never delete
  `com.apple.coredata.cloudkit.zone` (Core Data purges the local store); deploy the schema to
  Production before shipping.
- A build can't be swapped while the version is Waiting for Review: the owner removes it first.

## Evidence before claims

- Don't state a diagnosis from weak evidence (a commit message, "models look compatible", remembered build
  numbers). Read the service logs, load the store, check `git branch --contains <fix>` / `merge-base` to see
  whether a fix actually reached `main` before blaming a regression elsewhere.
- Prove a change with a debug build on the device; don't ship TestFlight builds to test.
- When something fails twice, stop looping and re-derive from evidence.

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Find the section above that applies and follow it. Ask the owner before anything outward-facing that is
   theirs to decide: merges, submissions, attestations, deleting remote state.
3. Reply with the outcome and its evidence. PenguPool records the work; write no log.
4. If the owner stated a lasting rule, propose it (`AGENTS.md` rule 2).
