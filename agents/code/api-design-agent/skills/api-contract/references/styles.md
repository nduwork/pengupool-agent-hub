# Interface styles and idempotency

## Picking a style

| Style | Fits when | Watch for |
| --- | --- | --- |
| REST over HTTP | Public or partner APIs, resource-shaped data, caching matters, many client languages | Chatty clients that need five calls for one screen |
| GraphQL | Several client apps with different data needs over one graph; a team owns the schema | Unbounded queries, N+1 resolvers, caching is harder |
| RPC (gRPC, JSON-RPC) | Service-to-service inside one organisation, streaming, strict typing across languages | Browser support, verbs leaking into a huge flat method list |
| Module interface | Callers live in the same process or repo | Treating it as "not an API" and skipping the contract |
| Events / messages | The producer must not wait for or know its consumers | Ordering, duplicates, schema evolution, no reply channel |

Choose one per surface and record why in an ADR. Mixing styles on one surface doubles the rules
callers must learn.

## REST

- Method meaning: GET reads and changes nothing; PUT replaces the whole thing and is
  repeatable; PATCH changes the listed fields only; DELETE removes and is repeatable; POST
  creates or runs an action and is not repeatable unless keyed.
- Status codes the caller can act on: 200 read/update, 201 created (with `Location`), 202 accepted
  for later (with a status URL), 204 nothing to return, 400 malformed, 401 not signed in, 403
  not allowed, 404 not there, 409 state conflict or version mismatch, 412 failed precondition,
  422 well-formed but invalid, 429 slow down, 5xx server's fault.
- Optimistic concurrency: return an `ETag` or `version`; accept `If-Match` on updates and answer
  412 (or 409) on a stale write.
- Long work: POST returns 202 and a job resource the caller polls; do not hold a request open.
- Bulk operations return a per-item result list; one bad item should not hide the others.
- Sparse fields (`fields=`) and expansions (`expand=`) only when a real caller needs them.

## GraphQL

- Design the schema from client use cases, not from tables.
- Nullable by default for fields that can fail independently; non-null only where absence is a
  bug. Making a field nullable later is breaking for clients.
- Mutations take a single input object and return a payload object that can carry the changed
  entity and user-facing errors (or a result union of success and error types).
- Connection-style cursor pagination for lists. Limit depth and cost per query.
- Deprecate fields with the `@deprecated` directive and a reason; remove only after usage drops.

## RPC

- Methods are verbs on a named service (`OrderService.CancelOrder`); requests and responses are
  dedicated messages per method, never shared, so each can grow alone.
- In protobuf, never reuse or renumber a field tag; reserve removed tags and names. New fields
  are optional by nature; old readers skip them.
- Use the standard status codes (`INVALID_ARGUMENT`, `NOT_FOUND`, `ALREADY_EXISTS`,
  `FAILED_PRECONDITION`, `UNAVAILABLE`…) with structured details, not a string in a success reply.
- Set deadlines on every call and say which methods are safe to retry on `UNAVAILABLE`.

## Module interfaces

- The public surface is what the package exports; everything else is private. Keep it small.
- Accept the narrowest input type, return a concrete, documented type. Typed IDs (distinct types
  for `UserId` and `OrderId`) catch swapped arguments.
- Pick one failure style per module (raise typed errors, or return a result type) and keep it.
- Version with the package (semantic versioning); a breaking change is a major bump.

## Events

- Name events in the past tense for facts (`OrderPlaced`); include an event id, the time, the
  schema version and the entity id.
- Consumers must handle duplicates and out-of-order delivery; no broker gives exactly-once across
  a consumer crash.
- Evolve the schema by adding fields; a breaking change is a new event type.
- Write the state change and the outgoing event in one transaction (an outbox table), or you
  will lose or invent events on a crash.

## Honouring an idempotency key

Accepting a key tells the caller that retrying is safe. If the server does not really honour it,
that is worse than having no key.

1. **The caller makes the key once per intent** and reuses it on every retry of that intent. A
   key built from a fresh random value or timestamp per attempt protects nothing; a key built
   only from the amount or user merges two real requests into one.
2. **Claim the key in one atomic step**: insert it under a unique constraint and let the
   constraint decide who wins. Reading "not seen yet" and then inserting is a race.
3. **Store a hash of the request with the key.** The same key with a different body is a client
   bug: reject it (422) rather than replaying the first answer.
4. **Decide what a duplicate gets while the first is still running**: reject with 409 and let the
   caller retry, wait a bounded time for the result, or return 202 with a status link. Never let
   it through because the first looks stuck.
5. **Plan for "unknown".** A timeout says nothing about whether the effect happened. Record the
   intent before calling out, so a crash leaves something to reconcile instead of a silent
   second effect.
6. **Keep keys longer than the longest retry path**, including queue redelivery and replay from a
   dead-letter queue, not just the client's retry window.
