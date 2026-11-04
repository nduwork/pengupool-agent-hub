# Playbooks (pick by need)

Part of the research-agent skill; pick the one that matches the request.


- **Workflow design** — actors, states, triggers, transitions; happy path, retries/idempotency,
  concurrency/ordering, human-in-the-loop, observability, acceptance criteria; include a Mermaid diagram.
- **Function / API design** — constraints and callers; survey existing repo patterns + one or two
  idiomatic references; propose signature/types, errors, edge cases, side effects, test plan,
  migration; give the signature first.
- **Datasource discovery** — criteria (coverage, granularity, freshness, volume, latency, cost,
  licence, access, stability, rate limits); longlist → scored matrix; verify access/terms at the
  primary source; provide a sample query and a fallback.
- **Repo / tooling setup** — existing conventions first; reference implementations; integration
  points and risks; smallest reversible phased steps with rollback.
- **Decision / trade study** — 2–3 options, weights that encode the decision, constraints as
  eliminators, anti-patterns named; `templates/trade-study.md`.
- **Brainstorm / idea generation** — divergent list (include the obvious, the do-nothing baseline,
  the cross-domain borrow, and the strange), cluster, converge on 2–3, stress-test, recommend a
  first step.
