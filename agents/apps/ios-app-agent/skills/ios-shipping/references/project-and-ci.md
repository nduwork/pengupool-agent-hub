# Project, signing and CI in practice

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## Project, signing and CI setup in practice

- The `.xcodeproj` is regenerated and gitignored, so `Package.resolved` isn't committed and CI re-resolves
  SwiftPM each build: pin `exactVersion` or vendor. Info.plist keys go in `project.yml` `info.properties`.
- Targets: app, widget/Live Activity extension (`NSSupportsLiveActivities`), unit tests, and a UITests scheme
  kept **out** of the CI scheme (fast, deterministic CI).
- Release: `CODE_SIGN_STYLE: Manual`, "Apple Distribution", profile "<bundle> AppStore". Debug: identity `-`
  and empty profile specifier, so simulator/test builds need no signing. `ITSAppUsesNonExemptEncryption: false`
  skips export compliance; `UIBackgroundModes: [audio]` keeps recording alive with the screen off.
- Upload blockers: missing iPad icon sizes or fewer than 4 orientations. iPhone-only (`TARGETED_DEVICE_FAMILY: 1`)
  also means no iPad screenshots.
- **No provider keys in Release builds.** The backend URL is a build setting (empty = feature off); Debug can
  point at a stub via launch args. The provider's spend limit is the real defence against a leaked key.
- One static `IOS_PROVISIONING_PROFILE` can't sign a second (extension) target: a `signing` lane registers both
  bundle IDs and creates/downloads both App Store profiles via the API. The API key usually can't create the
  app record (403); create it once in the ASC web UI.
- Leave `MARKETING_VERSION` alone between betas so beta approval carries over. Internal testers need no beta
  review; external testers need the privacy URL on `betaAppLocalizations` (not `appInfoLocalizations`) plus review.
- "MAC verification failed … wrong password": the `.p12` and its password are out of sync; re-export both.
- **Verification must assert against Apple's API and exit non-zero** (re-read the group; fail if the build
  isn't in it). A vanished `/tmp` helper once printed blank lines and an attach was logged as done.
- Verify the backend with the app's **real request shapes** (strict schema, streamed and non-streamed) and
  call every action, especially the expensive one: notes returned 200 while every report returned 502.

## Swift 6 concurrency

- Settings that worked: Swift 6.0, `SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor`, `SWIFT_APPROACHABLE_CONCURRENCY: YES`.
- Default MainActor applies to your target, not dependencies. A closure touching MainActor state is inferred
  `@MainActor` and fails when passed to a nonisolated, non-Sendable escaping parameter. Fixes:
  `@preconcurrency import`, a nonisolated handler that hops with `Task { @MainActor in }`, or a binding-based
  API. Spike a dependency before committing to it.
- With approachable concurrency a plain nonisolated `async` func runs on the **caller's** actor; mark heavy
  work `@concurrent`. `CIContext`/`CIImage` are thread-safe, `CIFilter` isn't (new one per call). Cross actors
  with Sendable values (`CGImage`, `Data`). Prefer Vision's Sendable request structs over `VNImageRequestHandler`.
- No public API opens the system Photos editor on app-supplied bytes; build crop/perspective in-app.
