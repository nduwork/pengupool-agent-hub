# Local tooling traps

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## Local tooling traps

- Local `bundle exec fastlane` can fail on a bundler mismatch with the system Ruby; CI uses Homebrew Ruby.
  Locally, use the Python API client instead.
- With `xcodebuild -derivedDataPath`, the `.app` is named after `PRODUCT_NAME` (may contain spaces), not the
  scheme; `find … -name "*.app"` before `simctl install`.
- SwiftUI: `.task` on a view that renders nothing (an empty `Group`) never runs; attach it to a container
  that always exists.
- Stage files by path when committing; owners often keep uncommitted work in the tree.

- Upload is not distribution: attach the build to the TestFlight group and verify. Map builds to commits via
  the workflow run's `headSha`, never from memory.
- Dev-signed install over a TestFlight install keeps data; going back needs delete + reinstall (TestFlight
  shows "Install", not "Update"), losing data not synced to the matching CloudKit environment.
- devicectl: `device install app`; `device process launch --terminate-existing <bundle> -- -arg` (`--` needed).
  `--console` shows stdout/stderr only; os_log needs `sudo log collect --device-name …` (owner runs it). Device
  must be unlocked.
- After an Xcode auto-update every git/xcodebuild/python3 shim fails until the owner runs
  `sudo xcodebuild -license accept` in a real Terminal (`!` has no TTY for sudo), then `xcodebuild -runFirstLaunch`.
- Disk full (shared cache symbols) breaks even tool output. Move `~/Library/Developer/{Xcode/iOS DeviceSupport,
  Archives,CoreSimulator}` to a data volume with symlinks (then `simctl shutdown all && simctl erase <udid>`);
  use `-derivedDataPath` on the big volume.
- Self-hosted runner is the dev Mac: CI queues behind local builds.
