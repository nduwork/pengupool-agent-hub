# Identity, purchases and App Review

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## Identity, purchases and App Review

- Sign in with Apple; anonymous until sign-in. Key users by the stable uid (Apple subject), never email.
  Sign-in **links** to the anonymous account, never replaces it (swapping ids loses credits); keep identity in
  its own documents (writing it into the ledger once wiped every token).
- Restore purchases must work across reinstall/devices, and in-app account deletion is required.
- App Attest doesn't run in the simulator: optional in Debug, service must work without it. Add it before any
  public beta or free credit grant (account farming is money farming).
- Consumable IAP packs at fixed Apple price points, with bonus credit; show users a unit they understand
  ("reports"), not tokens.
- StoreKit 2 client (Agenton tip jar, shipped 1.1): a local `.storekit` file in the scheme tests without ASC;
  `finish()` only `.verified` transactions; a `Transaction.updates` listener finishes out-of-band ones. A
  compile flag in `project.yml` lets IAP be cut from a release without deleting code.

- Credit packs (research, Apple docs, 2026-10-05; not yet lived):
  - Credits may never expire (3.1.1).
  - StoreKit doesn't restore consumables, so keep an append-only server ledger tied to the account, with
    one unique row per `transactionId`.
  - Order: verify the JWS → commit the row → `finish()`.
  - Reject a mismatched `appAccountToken`.
  - On REFUND or revoke, append a negative row with the balance floored at 0; re-credit on REFUND_REVERSED.
  - Keep free grants as a separate ledger source.
  - In the UI, "Sign in to see your balance" beats a Restore button.
  - Anything bought that stays in the account must stay account-bound; say so in the review notes.

**First paid IAP: checklist from Apple's documented flow. No app here has lived it yet, so check each step
and move it into the verified list above once done.**
1. ASC > Business: sign the Paid Apps agreement, add bank and tax details. Products don't load (even in
   sandbox) until it shows Active. Owner's clicks; record how long it took here.
2. Each consumable needs a product ID (never reusable), reference name, price, a display name and description
   per locale, a review screenshot and availability (see [asc-api.md](asc-api.md)). Submit the first IAPs **with** an app version (select them on the
   version page). Later ones can be submitted alone.
3. Sandbox: create testers in ASC > Users and Access > Sandbox, sign in on the device under Settings >
   Developer (or App Store) > Sandbox Account. TestFlight builds don't use sandbox accounts: purchases are
   free with the normal Apple ID (verified on a shipped app). A new IAP can take hours before
   `Product.products` returns it.
4. Server: verify the signed JWS transaction against Apple's root CA (App Store Server Library), and check
   `bundleId`, `environment` (Sandbox vs Production; App Review buys in Sandbox, so production servers must
   accept both) and the `appAccountToken` you set (a UUID). The App Store Server API uses an In-App Purchase
   key (ASC > Integrations), not the ASC API key. Set the Server Notifications V2 URLs for Production and Sandbox
   in App Information. Credit idempotently by `transactionId`; `finish()` only after the server credits.
5. Common rejections: a missing Restore button (required for non-consumables and subscriptions; for consumables,
   restore credit through the account), products that fail to load during review (usually
   the agreement or missing metadata), and prices or wording that differ from the store listing.
- App Review can't sign in with Apple: ship a demo mode in the same binary (separate root view, fabricated data,
  in-memory container, scripted clients) that can never start real work and clears on exit.
