---
name: architecture-choice
description: Choose a structure for a service or system (layered, hexagonal, modular monolith, separate services, event-driven) from the forces at hand, draw module and service boundaries, set dependency rules, and decide when not to split. Use when starting a new service, when a codebase has tangled dependencies, or when someone proposes splitting into services or adding a queue.
triggers:
  - architecture pattern
  - hexagonal
  - clean architecture
  - modular monolith
  - microservices
  - should we split
  - service boundary
  - bounded context
  - dependency cycle
  - event-driven
---

# Architecture choice

The goal is the simplest structure that keeps the code easy to change for the forces this
system actually has. Name the forces first; the pattern follows from them.

## 1. Name the forces

Write down, with evidence from the task or the repo:

- **Change**: which parts change often, and together? Which change for different reasons?
- **Teams**: how many teams touch this, and do they need to ship independently?
- **Load**: does one part need to scale, fail or be deployed differently from the rest?
- **Consistency**: which data must change together in one transaction?
- **Integrations**: how many external systems (databases, vendors, queues) sit at the edges, and
  how likely is one to be swapped?
- **Testing**: can the core rules be tested without a database or network today?
- **Constraints**: language, platform, regulatory or ops limits the owner has set.

If a force is a guess ("we might need to scale"), mark it as a guess. Guesses do not justify
distribution.

## 2. Pick the shape

Move down this ladder only when a named force requires it:

1. **Plain layered module**: handler → service → data access, one deployable. Fits small
   systems with one team and few integrations.
2. **Ports and adapters (hexagonal)**: the domain core defines the interfaces it needs; database,
   HTTP, vendors are adapters at the edge. Fits when there are several integrations, a likely
   swap, or core rules that must be tested without infrastructure. Do not add a port for a
   dependency that has one implementation and no test pain.
3. **Modular monolith**: one deployable, several modules with enforced boundaries, each owning
   its data and exposing a small interface. Fits several teams or subdomains that still deploy
   together. Usually the right answer to "should we use microservices?".
4. **Separate services**: split a module out only when it needs independent deploys, scaling,
   failure isolation or a different tech stack, and its boundary has been stable inside the
   monolith. Each service owns its data; no shared database.
5. **Event-driven between parts**: when producers must not wait for or know consumers, or work
   must survive a consumer being down. Costs: eventual consistency, duplicate handling, harder
   debugging.

Details, warning signs and migration steps for each are in
[references/patterns.md](references/patterns.md).

## 3. Draw the boundaries

- Cut along business capability or subdomain, not along technical layers ("the database
  service" is not a boundary).
- A boundary owns its data. Others read it through its interface, never its tables.
- Data that must change in one transaction belongs inside one boundary. If two boundaries need
  a shared transaction, the line is in the wrong place.
- Use the domain's own words inside each boundary; translate at the edge where two models meet.
- Write the dependency rule in one line per boundary ("`billing` may call `accounts`; nothing
  calls `billing` except the API layer") and say how it will be checked (import linter, module
  visibility, a test, or review).

## 4. When not to split

Say "don't split" when any of these is true:

- One team owns all of it and deploys it together.
- The boundary is still moving; you would be freezing a guess into a network call.
- The parts share data that must stay consistent in one transaction.
- There is no ops capacity for more deployables, tracing and on-call.
- The pain is really tangled code; a module boundary inside the monolith fixes that for less.

## Output

A short design note in the owned path:

1. Forces (with evidence or marked as guesses).
2. Options considered, two or three, each with cost and what it buys.
3. The choice, the boundaries (a list or small diagram), and the dependency rules.
4. What would make you revisit it ("revisit if checkout needs to deploy daily on its own").

Then record the choice as an ADR with the `decision-records` skill. Do not restructure code;
the implementer does that.
