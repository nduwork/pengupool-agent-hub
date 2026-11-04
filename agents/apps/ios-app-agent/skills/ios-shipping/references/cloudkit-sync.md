# SwiftData + CloudKit sync

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## SwiftData + CloudKit sync

- CloudKit rejects a store with non-optional relationships. Fix without a migration: keep the stored
  property **name**, make it optional (`var segments: [Segment]?`), add a computed non-optional view
  (`segmentList`) and move call sites to it. Never rename stored relationships; drive the change from compiler
  errors, not a regex (other types share member names). Attributes need defaults; no unique constraints.
- Open with `ModelConfiguration(cloudKitDatabase: .private(id))`; on throw, fall back to `.none` on the same
  file so a sync fault never costs data. That fallback is silent: **load the CloudKit store on a device and
  read the console before claiming sync works.**
- Debug/simulator builds are not iCloud-signed: gate sync behind a launch arg (`-cloudSync`) plus a user
  setting (default on, applies next launch). Settings that worked: toggle with a data-loss confirmation,
  iCloud status (`CKContainer.accountStatus`), last upload (`NSPersistentCloudKitContainer.eventChangedNotification`),
  "Sync now". Start the `eventChangedNotification` observer **at app launch**, not lazily from Settings: the
  fatal export happens right after launch, and a late observer leaves an old "Synced" time showing with no
  error. A "Sync now" that re-saves a property with its own value saves no change and uploads nothing, so
  don't let the UI claim a sync.
- **Two environments.** Development-signed builds write Development; TestFlight/App Store use Production,
  which starts empty and gets its schema only via CloudKit Console > "Deploy Schema Changes…" (enabled while
  viewing Development). No CLI/API promotes to Production (`cktool import-schema` is Development-only). Owner's
  click.
- **`CD_<attr>_ckAsset` trap (CKError 2 in Production, deploy shows 0 changes).** Mirroring moves a large
  String/Data value into a separate Asset field `CD_<attr>_ckAsset`, created in Development only the first
  time a large value is exported. This includes `.externalStorage` Data: a small value goes to `CD_<attr>`
  (BYTES), a large one to `CD_<attr>_ckAsset`. Symptom: small or empty records sync, while large ones fail
  with CKError 2 plus `atomicFailure` across the batch. If Development never saw a large value, Production
  rejects the record: "Cannot create or modify field 'CD_x_ckAsset' … in production
  schema". Fix: in Development add the field (type Asset, index None), deploy, relaunch the app (mirroring
  stops retrying until next launch). Prevent: pre-add **both** `CD_<attr>` and `CD_<attr>_ckAsset` for
  every String/Data attribute that can grow large (photos too), or run `initializeCloudKitSchema` in a Debug build before release.
  The reverse case is just as bad. If only `_ckAsset` reached Production, sync works until the first value
  small enough to go inline. Then that write fails with 12/2006, the rest of its batch fails with 1011
  atomicFailure, the delegate logs "Never successfully initialized", and nothing syncs. Before shipping, check
  that every `*_ckAsset` field in `cktool export-schema` has its base field, e.g.
  `awk '{gsub(/"/,"")} /_ckAsset/{n=$1;sub(/_ckAsset$/,"",n);a[n]} /BYTES|STRING/{b[$1]} END{for(k in a)if(!(k in b))print "missing",k}' x.ckdb`
  (tested on a hand-written sample, not a real export; it matches names across all record types).
- CKError 2 is a partial failure; the top-level text hides the cause. Surface it in the app from
  `CKError.partialErrorsByItemID` plus each error's `NSDebugDescription`, unwrapping the `NSUnderlyingError`
  Core Data wraps around it. Or read the device log: `sudo /usr/bin/log collect --device-udid <UDID> --last
  15m --output x.logarchive` (real Terminal for sudo; `/usr/bin/log` because zsh has a `log` builtin), then
  `log show --archive x.logarchive --predicate 'process == "<App>" AND eventMessage CONTAINS[c] "error"'`.
- **Production fields are permanent:** they can't be changed or deleted, so a wrong type (ASSET instead of
  BYTES) stays forever. Fix: **add** a new attribute with a new name, keep the old one in the model, and on
  store open move values from old to new and set the old to nil. Diff types with `cktool export-schema`
  **before** deploying.
- **Only additive model changes in a CloudKit store:** never rename or remove a property once the store has
  synced. `@Attribute(originalName:)` crashes at launch with NSCocoaErrorDomain 134110 ("Properties cannot be
  renamed in stores that are used with CloudKit"). The simulator doesn't reproduce it (Debug builds there
  have no iCloud entitlement), so test on a device.
- **Never delete `com.apple.coredata.cloudkit.zone` to "reset" sync.** Core Data reads it as a user wipe and
  purges the local store. An app's user data was lost this way.
- `xcrun cktool`: create a management token in CloudKit Console > Tokens & Keys. Non-interactive shells
  can't answer the hidden prompt, so run `xcrun cktool save-token <TOKEN> --type management`, then
  `get-teams` and `export-schema --team-id <T> --container-id <C> --environment production|development
  --output-file x.ckdb`. That gives the real schema as text, the fastest diff against the model.
- Device log, per-record cause: cloudd's lines are redacted, but the **app** process's
  CKModifyRecordsOperation line carries the server message. Search with
  `log show x.logarchive --predicate 'process == "<App>"'` for "server message". Use `--last 3h` when the
  failure isn't at launch.
- Device log tips: force-quit and relaunch the app just before `log collect --last 2m` so the startup errors
  are inside the window. `/usr/bin/log show` needs the agent sandbox disabled. Field names show as `<private>`,
  but cloudd logs "Received error N" / "Syntax error in request" with a request UUID. Look that UUID up in
  CloudKit Console > Logs (Production) to get the operation, error and record type (not the field).
- The Console shows only your own Apple ID's private DB. Proof of sync: delete app, reinstall the same-signed
  build, data returns. On-phone: Settings > iCloud > Manage Account Storage (app list, not Backups). Local
  size: `xcrun devicectl device info files --domain-type appDataContainer --domain-identifier <bundle>`.
- Deleting an app deletes its data; iCloud Backup restores only on a whole-device restore.
