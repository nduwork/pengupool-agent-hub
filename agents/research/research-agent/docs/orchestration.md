# How PenguPool orchestrates sessions, and how a research agent is summoned

Findings from reading the PenguPool source (`nduwork/pengutool`)
(package `pengupool`, v0.5.1). References are `file:line` in that repo.

## 1. The session model

- A **session** is a live Claude Code (`cc`) or pi (`pi`) process. PenguPool discovers it from
  per-harness live files and builds a tree (`pengupool/model.py`, `pengupool/routing.py:23`).
- **Grouping** is a flat map `childSessionId -> parentSessionId` in
  `~/.pengupool/groups.json`. A session has **at most one parent**; harnesses never mix
  (`pengupool/routing.py:23`, `pengupool/ctl.py:214`).
- **Roles** live in `~/.pengupool/profiles/<sid>.json` (`pengupool/profiles.py`): `summary`,
  `responsibility`, `keywords`, `workspace`, and who last edited them.
- **Context injection**: before each prompt, a `<pengupool>` block is appended describing the
  session's place in the tree, its parent/children, roles, the triage rule and the routing rule
  (`pengupool/context.py`, pi via `pengupool/pi_extension.ts`, Claude via its prompt hook).

## 2. Routing rules (enforced)

- A grouped session may message **only its parent or its direct children**
  (`pengupool/routing.py:159` `authorize_send`). Anything else is refused with the valid
  recipients and the next hop named.
- Enforcement points: Claude `PreToolUse` on `SendMessage`; pi `tool_call` on
  `intercom` send/ask → `pengupool ctl authorize` (exit 3 blocks) (`pengupool/pi_extension.ts`).
- **Hop-by-hop**: to reach a non-adjacent session, a session sends one edge toward it;
  `pengupool ctl route <sid> <target>` returns the next hop (`pengupool/routing.py:71`,
  `pengupool/ctl.py:336`). Requests carry `request_id, origin, target, objective, context,
  reply_path, hop_limit`; replies travel back along `reply_path` (`pengupool/context.py` RULES).
- A child never hands work upward; it **inquires** of its parent, who triages the inquiry.

## 3. Triage, roles and matching (soft)

- Every grouped reply begins with a `Triage:` line (`Triage: mine`, `Triage: → <session>`,
  `Triage: asked parent`) (`pengupool/context.py`).
- A role-less session is told `ROLE REQUIRED` until it runs
  `pengupool ctl describe <sid> --summary … --responsibility … --keywords …`.
- When a user prompt matches a child's keywords/name/workspace/role, the parent is shown
  `ROUTE CHECK` with the matched words — a **hint**, not a gate (`pengupool/context.py`
  `route_match`, `ROUTE`).
- "do it yourself" / "don't delegate" disables the check for that prompt (`SELF` regex).

## 4. Who may change what (permissions)

| Operation | Who may do it | Where |
| --- | --- | --- |
| `describe` a session's role | the session itself, or its direct parent, or the user | `profiles.py:150-158` |
| `group` / re-parent | **user only** (a session is refused) | `ctl.py:214-219` |
| `slash` compact/rename another session | **user only** | `ctl.py:264` |
| `new` (spawn a session) | not caller-guarded; runs a tmux window | `ctl.py:74`, `ctl.py:373` |
| `route`, `authorize`, `tree`, `profile`, `context` | any session | `ctl.py` verb table |

Consequence: **a research session cannot attach itself to a parent, and cannot be the child of
two parents at once.** Re-parenting or spawning+grouping is a user/editor action.

## 5. The temporary direct line (@tag)

The user may write `@research-agent` in a prompt. PenguPool records a grant for that prompt
and lifts the adjacent-only rule **both ways** between the session and the tagged session
(`routing.py:123-157` `grant`/`granted`; TTL `GRANT_TTL = 3600s`, cleared by the next prompt).
Grants are only opened from the prompt hook, which sees what the user typed (the pi extension
proves this with an in-memory secret). So @tag is the cheap, no-restructure way to open a
direct line for one exchange.

## 6. Summon patterns for a research agent

Because of §4, a single research session can serve **one** parent directly. Choose:

### A. @tag one-off (default for single questions)
User types `@research-agent <question>` into the requesting session's prompt. The requester may
`intercom ask research-agent …` and receive a reply in-turn. No restructuring, no repo change.
Best for: a datasource check, a naming/API question, a "where is X documented".

### B. Re-parent the shared singleton
User drags `research-agent` under the requester (or `pengupool ctl group <me> <requester>` run by
the user). The requester now messages directly, no user involvement per ask.
Best for: a sustained stream of research for one session. Limits: one parent at a time, serial.
Because a re-parent swaps the requester, it must trigger the context refresh protocol
(`skills/research-agent/references/context-continuity.md`): re-check authority and drop the previous
requester's private/relationship context before answering the new parent.

### C. Spawn-per-request (best for parallel/isolated research)
User starts a fresh research session under the requester (`n` then `g` in the PenguPool view, or
`pengupool ctl new <dir> <name> …` + user `ctl group`). This repo's skill/templates make each
spawn consistent.
Best for: several requesters at once, or research with its own long budget/context.

### D. Route-to-hub (shared long-lived service)
Keep `research-agent` under a common ancestor (e.g. the pool root). Any session routes a request
one hop at a time up/down (`ctl route`). No user action, but every hop costs a triage decision and
latency; use explicit `request_id`/`reply_path`/`hop_limit`.
Best for: a stable service with many occasional requesters and a cooperating tree.

### Recommended
@tag for one-offs → spawn-per-request for parallel work → route-to-hub when a permanent shared
service is wanted → re-parent only for a single sustained requester. This ordering needs no
PenguPool change today.

**Intended long-lived shape** (confirmed by `pengutool`): a **hub parent with one stable child
per research domain**. The hub keeps its children's roles current with `ctl describe --keywords …`
so the prompt hook's `route_match` picks the right child per request — no re-parenting, no new
feature. Use `@name` only for a one-off direct line.

## 7. Confirmed: no dynamic attach (and the authoritative doc)

Asked `pengutool` whether PenguPool would gain dynamic attach/re-parent or multi-parent support.
Answer: **no**, and none is planned — it is a deliberate design choice.

- One parent is structural: `groups.json` is `child -> parent`, and `apply_groups` drops every
  derived edge into a grouped child, then prepends the single manual edge (`model.py:816-838`).
- `group_error` refuses dead sessions, self-parenting, cycles and cross-harness edges (`model.py:843-868`).
- `ctl new` takes no parent argument: new sessions always start **top level** by design
  (`ctl.py:74-87`, verb table `376-379`).
- `ctl group` is user-only (`ctl.py:214-237`); the guard is process-tree based (`profiles.py:104-118`),
  so it is best-effort, not a cryptographic token.

The authoritative design is `PenguPool/docs/group-session-framework.md` (in the `PenguPool`
checkout, not `pengutool`). Its *Decisions to review* #1 is exactly: "a new session starts at the
top level. The user moves it under another session." The production code has one departure from
the proposal worth knowing: routing guidance is `ROUTE CHECK` (a hint), not a blocking
`ROUTE REQUIRED` (see `CHANGELOG.md` 0.3.3).

Until PenguPool changes: **the user performs attach/group.** The research-agent contract is built
around the four patterns above.
