# Credentials and CI

The owner creates and stores every credential (certificates, app-specific passwords, API keys).
The agent refers to them by name only: a keychain profile, a CI secret name, a file path.

## The certificate

- Only a **Developer ID Application** certificate works outside the Mac App Store. Apple
  Development and Apple Distribution certificates look usable, but notarization rejects them.
  Check: `security find-identity -v -p codesigning | grep "Developer ID Application"`.
- Only the team's **Account Holder** can create it. Easiest: Xcode › Settings › Accounts › the team
  › Manage Certificates › + › Developer ID Application (the private key stays in this Mac's
  keychain). Or developer.apple.com › Certificates › + with a CSR from Keychain Access. If the option
  is greyed out, someone without the Account Holder role is signed in.
- The **Team ID** is the OU, the ID in parentheses on a Developer ID or Distribution certificate.
  The parenthesised ID on an *Apple Development* certificate is a personal ID, not the team.
- Two certificates with the same name (an old and a renewed one) make a name ambiguous: use the
  SHA-1 hash from `security find-identity -v -p codesigning` as the identity.

## Where each secret lives

Master copies are in the owner's password manager. Everything else is a copy.

| Secret | Local Mac | CI secret |
| --- | --- | --- |
| Developer ID Application certificate + private key | login keychain | `CSC_LINK` (base64 `.p12`), `CSC_KEY_PASSWORD` |
| App Store Connect API key `AuthKey_<KEYID>.p8` | inside the notarytool profile (or `~/.appstoreconnect/private_keys/`, chmod 600) | `APPLE_API_KEY_BASE64` (base64 `.p8`), `APPLE_API_KEY_ID`, `APPLE_API_ISSUER` |
| Apple ID app-specific password (alternative to the key) | inside the notarytool profile | `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID` |
| Temporary keychain password (hand-rolled CI only) | — | generated per run, never stored |

Rules: never `cat` a `.p8` or `.p12`, never echo a secret in a workflow, decode into
`$RUNNER_TEMP` or a `mktemp` path, never into the repository. Prefer the API key: one key serves
local and CI, and it is not tied to a person's Apple ID.

## Local: notarytool keychain profile (default)

The owner runs once, in a terminal of their own:

```sh
xcrun notarytool store-credentials notary \
  --key <path/to/AuthKey_KEYID.p8> --key-id <KEYID> --issuer <ISSUER-UUID>
```

The key comes from App Store Connect › Users and Access › Integrations › Keys: a Team key with the
Developer role. It downloads once only.

The Apple ID form needs no key file: `xcrun notarytool store-credentials notary --apple-id <email>
--team-id <TEAM>`, and the owner pastes an app-specific password made at account.apple.com when
it prompts. Either way the secret goes from the owner straight into the keychain, never through an
agent or the repository.

Check with `xcrun notarytool history --keychain-profile notary` or `scripts/macos-release.sh
preflight`; "No submission history" on a new account means it works. A 401 means the key is stale
or revoked; a misleading 401 can also come from accelerated upload: retry with
`--no-s3-acceleration`.

Notarization is an automated malware scan, not App Review: usually minutes, sometimes up to an
hour. A new team's first submission takes tens of minutes; don't treat that as a hang.

## CI (GitHub Actions)

- Runner: a hosted `macos-15` (pinned) or a self-hosted Mac. Signing on a shared self-hosted Mac
  must not touch the login keychain: use a temporary keychain per run.
- **electron-builder**: set `CSC_LINK`, `CSC_KEY_PASSWORD`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER`
  and `APPLE_API_KEY`. It creates and deletes a temporary keychain itself. On v26 the
  `APPLE_API_KEY` environment variable must be a **path** to the `.p8` file; base64 does not work.
  Decode the `APPLE_API_KEY_BASE64` secret into a `mktemp` file and export its path. Never map the
  secret straight into `APPLE_API_KEY`: notarization then fails.
- **Hand-rolled** (Xcode or the script):

  ```sh
  KC="$RUNNER_TEMP/signing.keychain-db"; KCPW="$(uuidgen)"
  security create-keychain -p "$KCPW" "$KC"
  security set-keychain-settings -lut 21600 "$KC"
  security unlock-keychain -p "$KCPW" "$KC"
  echo "$CSC_LINK" | base64 --decode > "$RUNNER_TEMP/cert.p12"
  security import "$RUNNER_TEMP/cert.p12" -k "$KC" -P "$CSC_KEY_PASSWORD" -T /usr/bin/codesign
  security set-key-partition-list -S apple-tool:,apple: -s -k "$KCPW" "$KC"   # or codesign hangs on a prompt
  security list-keychains -d user -s "$KC" $(security list-keychains -d user | tr -d '"')
  rm "$RUNNER_TEMP/cert.p12"
  KEY="$(mktemp)"; trap 'rm -f "$KEY"' EXIT; echo "$APPLE_API_KEY_BASE64" | base64 --decode > "$KEY"
  ASC_KEY_PATH="$KEY" ASC_KEY_ID="$APPLE_API_KEY_ID" ASC_ISSUER="$APPLE_API_ISSUER" \
    scripts/macos-release.sh notarize "<App>.dmg"
  ```

  Delete the keychain in an `always()` step: `security delete-keychain "$KC"`.
- **Release-env gate**: the first step of a release job fails when any signing or notary secret is
  empty, so a release never ships unsigned by accident. Local and pull-request builds skip signing
  and notarization to stay fast.
- Put the signing job in a GitHub Environment with required reviewers.
- Upload `<file>.notary-log.json` as an artifact. Stay under Apple's limit of about 75
  notarizations a day.
- Rotating the key or the certificate means updating every repository's secrets and the local
  profile; that is the owner's call.
