# App Store Connect API

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## App Store Connect API (when fastlane is overkill)

A ~20-line Python client signs an ES256 JWT (`iss` = issuer ID, `aud` = `appstoreconnect-v1`, header
`kid` = key ID, 20-minute expiry) from the `.p8` at `ASC_KEY_FILEPATH` and calls
`https://api.appstoreconnect.apple.com`. Useful calls:
- `GET /v1/builds?filter[app]=<appId>&sort=-uploadedDate&limit=1`: latest build and `processingState`.
- `PATCH /v1/appStoreVersions/<id>/relationships/build`: attach a build.
- `PATCH /v1/appStoreReviewDetails/<id>`: review notes and contact.
- `PATCH /v1/apps/<appId>` with `contentRightsDeclaration`: `USES_THIRD_PARTY_CONTENT` or
  `DOES_NOT_USE_THIRD_PARTY_CONTENT`.
- Screenshots: create an `appScreenshotSets` entry (`APP_IPHONE_67` covers 6.9"), reserve each
  `appScreenshots` with fileName and fileSize, PUT the bytes to the returned `uploadOperations`, then PATCH
  `uploaded: true` with the MD5 checksum.

- `GET /v1/bundleIds?filter[identifier]=X` is a **prefix** match (may return `X.web` first): pick the exact
  identifier from the list.
- API can enable `ICLOUD` (setting `ICLOUD_VERSION: XCODE_6`) and `PUSH_NOTIFICATIONS`, but **cannot create
  an iCloud container or assign it to an App ID** (portal only). Verify by creating a throwaway App Store
  profile, base64-decoding `profileContent`, checking `com.apple.developer.icloud-container-identifiers`, then
  deleting it. Profiles older than a capability fail signing; `get_provisioning_profile(force: true)` renews.
- Devices: `POST /v1/devices` (UDID from `xcodebuild -showdestinations`). CLI automatic dev signing:
  `xcodebuild … -allowProvisioningUpdates -authenticationKeyPath/-authenticationKeyID/-authenticationKeyIssuerID
  DEVELOPMENT_TEAM=… CODE_SIGN_STYLE=Automatic CODE_SIGN_IDENTITY="Apple Development" PROVISIONING_PROFILE_SPECIFIER=""`.
- Listing by API works (localizations, categories, age rating, screenshots). Review contact name/phone/email
  must be set together or the notes PATCH 409s. IAP consumables stay `MISSING_METADATA` until price, name,
  review screenshot **and availability** (`POST /v1/inAppPurchaseAvailabilities`, territories) are set. The
  priceSchedule body needs `included` at the top level and `baseTerritory` as a relationship. IAP review
  screenshot: 1242x2688 JPEG passed; 1179x2556 and 1290x2796 failed with `IMAGE_INCORRECT_DIMENSIONS`. The API
  (PyJWT ES256) also covers review details and attaching a build to a version.

**Not possible by API:** the App Privacy questionnaire, and pressing Add for Review / Submit for Review.
Those are the owner's clicks.
