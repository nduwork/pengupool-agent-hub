# Submission

Part of the ios-shipping skill; read it when [SKILL.md](../SKILL.md) points here.

## Submission gotchas

- "You must set up Content Rights Information": set `contentRightsDeclaration`. An app showing government
  data, third-party forecasts or CC photos uses third-party content. It is an attestation in the owner's
  name, so audit image licences first (credit, commercial-OK licence, source) and drop anything uncertain.
- A build cannot be swapped while the version is **Waiting for Review** (409 `INVALID_STATE`). The owner
  removes it from review, you attach the new build, they resubmit.
- Content that loads from a backend after approval is allowed (data, not code). Say so in the review notes.
  If the privacy label is "Data Not Collected", say that contact buttons only open the user's Mail app.
- Marketing screenshots at 1320×2868 (6.9") satisfy the required iPhone size.
- Background refresh needs `UIBackgroundModes: [fetch]`, a permitted `BGTaskScheduler` identifier, and a
  reschedule on every run. Pending local notifications are capped at 64.

## Worked example: an app's 1.0 (October 2026)

Builds were uploaded by dispatching `testflight.yml` on the self-hosted runner; each reached `VALID` within
minutes. Add for Review was first blocked by Content Rights, set by API after a photo-licence audit removed
six uncertain images. A late UI change then needed a new build while 1.0 sat in Waiting for Review: the
owner removed it from review, build 42 was attached with `PATCH …/relationships/build`, the review notes
were updated by API, and the owner pressed Submit.
