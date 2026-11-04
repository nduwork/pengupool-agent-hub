# Patterns in more detail

Each entry: what it is, the dependency rule, signs it is working, signs it is wrong.

## Layered

Handlers parse and format; services hold the rules; data access talks to storage. Calls go
down only.

- Working: a handler is short (parse, call one service method, map the result).
- Wrong: business rules in handlers or SQL; services importing web framework types; tests need a
  running database to check a rule.

## Ports and adapters (hexagonal) / clean / onion

The core (entities, rules, use cases) imports nothing from frameworks or drivers. It declares
the interfaces it needs (ports): "save an order", "charge a card". Adapters implement them:
a Postgres repository, a payment vendor client, an HTTP controller. Wiring happens in one place
at startup.

- Rule: imports in the core point only inward. Adapters depend on the core, never the reverse.
- Working: every use case runs in a unit test with in-memory fakes for its ports; swapping a
  vendor touches one adapter.
- Wrong: ORM or validation-library annotations on core entities (keep a separate storage model
  and map at the adapter); a use case importing a concrete adapter; a port per class "just in
  case".
- Cycle between layers: find the import that points outward and replace it with a port the
  core owns.

## Modular monolith

One deployable split into modules by subdomain. Each module has a public interface (a package
or facade) and private internals, and owns its tables.

- Rule: modules call each other only through public interfaces; no cross-module table access or
  joins. Enforce with the language's visibility rules or an import-lint check in CI.
- Working: a module can be reasoned about and tested alone; most changes touch one module.
- Wrong: a "common" or "shared" module that everything imports and that keeps growing; modules
  reaching into each other's tables.
- Migration path: this is the staging ground for services. A module whose interface has been
  stable for a while and that needs independent deploys is the candidate to extract.

## Separate services

Each service is deployed, scaled and owned on its own, with its own data store.

- Rule: talk over published contracts only (API or events); no shared database; each service can
  start and degrade without the others.
- Costs to name up front: network failures and timeouts on every call, distributed tracing,
  versioned contracts between teams, data duplication, more on-call surface.
- Wrong: services that must deploy together ("distributed monolith"); chains of synchronous calls
  where one slow service stalls everything; a shared database used as an integration point.
- Extracting one: put the module behind its interface in the monolith first, move its data
  ownership, route callers through the interface, then move the code behind a network call.

## Event-driven

Parts publish facts; others subscribe. Producers do not know consumers.

- Rule: events are past-tense facts with a versioned schema; consumers are idempotent and
  tolerate reordering.
- Use the outbox pattern: write the state change and the event row in one transaction, then
  publish from the outbox.
- Working: adding a consumer needs no change to the producer.
- Wrong: events used as remote procedure calls that wait for a reply; consumers that break on
  duplicates; no way to replay or inspect what was published.

## Where two models meet

When one boundary must use another's data or a vendor's model, translate at the edge: the
consumer keeps its own small type (`CustomerRef`, `ProductSnapshot`) and an adapter maps the
other side into it. This keeps a change in the other model from rippling through the consumer.

## Keeping aggregates small

A consistency boundary should hold only what must change together. Refer to other aggregates by
id, not by holding them. Cross-aggregate updates go through domain events or a coordinating use
case, accepting brief inconsistency.
