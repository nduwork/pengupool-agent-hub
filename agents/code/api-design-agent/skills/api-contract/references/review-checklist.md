# Contract review checklist

Run this against a draft or a diff. Report only what fails, worst first, as
`file:line — problem — why it matters — fix`. Mark each finding **breaking**, **risk** or
**polish**.

## 1. Compatibility (check first)

Compare against the last released contract (`git diff <base> -- <file>`):

- Any field, operation, enum value or error code removed or renamed?
- Any type changed, field made required, validation tightened, default changed?
- Any response field made nullable (GraphQL) or a protobuf tag reused?
- Does the contract tell callers to ignore unknown fields and tolerate new enum values?

Each yes is **breaking** unless every caller changes in the same commit. It needs a version or
new operation, a deprecation date and an ADR.

## 2. Shape and naming

- One casing and one naming scheme across the surface; matches the repo's other APIs.
- Plural nouns for collections; no verbs in REST paths; nesting at most one level.
- Inputs and outputs are separate types; no server-owned fields in create inputs.
- Variants modelled as tagged unions, not many optional fields.
- IDs opaque; times ISO 8601 UTC; money in integer minor units with currency.
- No database column names, internal service names or storage quirks leaking through.

## 3. Behaviour

- Each operation states: who may call it, inputs, output, every error, retry safety, an example.
- Side-effecting operations take an idempotency key or say they are unsafe to retry.
- Updates say whether they replace or patch, and how concurrent writes are detected.
- Long-running work returns a job/status handle instead of a held-open request.

## 4. Lists

- Every growable list is paginated, with default and maximum page sizes.
- Sort order is stable (unique tiebreaker); cursors are opaque.
- Filterable and sortable fields are listed.

## 5. Errors

- One error shape everywhere: stable code, message, optional field details.
- Status/code mapping is consistent; 4xx vs 5xx split is right; 401 vs 403 used correctly.
- Retryable errors are marked; throttling returns a retry hint.
- Nothing internal leaks (stack traces, SQL, hostnames); hidden resources do not reveal they exist.

## 6. Safety and limits

- Authentication and authorization stated per operation.
- No secrets or personal data in paths or query strings.
- Size limits on bodies, strings and arrays; rate limits stated.
- Examples use made-up data only.

## 7. Documentation

- The contract lives in the repo next to the code that serves it.
- Deprecated items carry a reason and a removal date.
- Decisions that shaped the contract link to their ADRs.
