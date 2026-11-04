---
name: api-contract
description: Draft and review API contracts for REST, GraphQL, RPC or in-process modules. Use when designing new endpoints or operations, changing a public interface, reviewing an OpenAPI/proto/GraphQL schema, or settling naming, pagination, error shape, idempotency and versioning before implementation starts.
triggers:
  - design an API
  - API contract
  - review this endpoint
  - OpenAPI review
  - breaking change
  - pagination design
  - error format
  - idempotency key
  - versioning strategy
---

# API contract

A contract says what a caller may send, what it gets back, and what can go wrong. Write it
before the code, keep it in the repo next to the code, and treat it as the spec the
implementation is tested against.

## Workflow

1. **Collect the facts.** Who calls this (browser, partner, another service, a library user)?
   What do they need to do, how often, at what size? What contracts and conventions already
   exist here? Reuse their naming, error shape and pagination; a second style is a defect.
2. **Model the nouns.** List the resources (or entities) and how they relate. Operations come
   from what callers do to them. If an action does not fit a noun cleanly (`approve`, `retry`),
   model it as a sub-resource or an explicit operation; do not bend it into an update.
3. **Write the contract** in the repo's format: OpenAPI for HTTP, `.proto` for gRPC, SDL for
   GraphQL, typed signatures for a module. For each operation give inputs, output, every error
   it can return, whether it is safe to retry, and one request/response example.
4. **Run the review checklist** in [references/review-checklist.md](references/review-checklist.md)
   on your own draft, then hand it over.
5. **Record the decisions** that shaped it (style choice, versioning scheme, auth model) with the
   `decision-records` skill.

## Design rules

**Naming**
- One casing per surface, matching the repo (often camelCase in JSON, snake_case in Python
  libraries). Never mix within one API.
- Collections are plural nouns; no verbs in REST paths. Nest at most one level
  (`/orders/{id}/items`); deeper lookups get their own top-level path.
- Booleans read as yes/no questions (`isArchived`, `hasChildren`). Times are ISO 8601 UTC with a
  suffix that says what happened (`createdAt`, `expiresAt`). Money is an integer of minor units
  plus a currency code, never a float.
- IDs are opaque strings to callers, even if they are integers inside.

**Inputs and outputs**
- Separate what the caller sends from what the server returns; server fields (id, timestamps,
  computed state) never appear in create inputs.
- Optional fields have a documented default. `null`, absent and empty mean different things only
  if the contract says so.
- Model variants as a tagged union (a `type` field) rather than a bag of optional fields.
- Validate at the boundary and nowhere else. Responses from third parties are untrusted input too.

**Lists**
- Every list that can grow is paginated from day one, with a default and a maximum page size.
- Prefer cursor pagination (`limit`, `cursor` → `nextCursor`) for data that changes or grows
  large; offset/page is fine for small, stable admin lists. Return a total only when it is cheap.
- Sorting must be stable: add a unique tiebreaker (usually id) to any sort key.
- Filters are query parameters named after fields; document which fields can be filtered.

**Errors**
- One error shape across the whole API: a stable machine code, a human message, and optional
  per-field details. Codes are part of the contract; message text is not.
- Map to the transport's status model (HTTP status, gRPC code, GraphQL error extensions or
  result unions) consistently. 4xx means the caller can fix it; 5xx means they cannot.
- Never leak stack traces, SQL, internal hostnames or whether a hidden resource exists (prefer
  404 over 403 when existence itself is sensitive).
- Say which errors are retryable, and send `Retry-After` (or the equivalent) when throttling.

**Retries and idempotency**
- Reads and deletes are naturally retry-safe; say so. Creates and other side effects either take
  an idempotency key or are documented as unsafe to retry.
- An accepted key is a promise: details of honouring it (atomic claim, payload check,
  in-flight duplicates, retention) are in [references/styles.md](references/styles.md).

**Versioning and change**
- Default: one live version, evolved by adding. Callers must ignore unknown fields and tolerate
  new enum values; say that in the contract.
- Breaking changes (remove, rename, retype, tighten validation, change a default or an error
  code) need a new version or a new operation, a deprecation notice with a date, and an ADR.
- Pick one version signal per API (path prefix, header or package name) and keep it.
- Unpublished or single-caller internal interfaces can change freely if every caller changes in
  the same commit; say which kind this is.

**Security at the contract level**
- Every operation states who may call it. Secrets and personal data never go in URLs or logs.
- Rate limits and size limits are part of the contract, not an afterthought.

## Output

The contract file in the owned path, plus a short note: what callers it serves, what is
breaking (or "nothing is breaking"), open questions for the owner, and which ADRs it relies on.
For a review: findings worst first, each with `file:line`, the problem, why it matters, and a
fix. A short report on a sound contract is a good result.

Style-specific notes (REST, GraphQL, RPC, modules) are in
[references/styles.md](references/styles.md).
