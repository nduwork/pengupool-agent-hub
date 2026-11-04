# Context continuity across requests

How this agent keeps a working context across many requests **without contaminating a new answer
with a stale or private one**. Read this whenever the requesting session changes, this session is
re-parented, or the same session starts a different subject.

The two triggers are **orthogonal** — solve them separately:

- a **different session** is a **trust-boundary** check (may *this* requester see *this* item?);
- a **different subject** is a **relevance** check (does *this* finding still apply to *this* task?).

Neither the session id nor topic similarity alone decides reuse. Decide **per layer and per finding**,
then assemble a fresh working context for the request.

## In short

- **Two orthogonal triggers**: a different session is a **trust-boundary** check; a different subject is
  a **relevance** check. Neither alone decides reuse.
- **Four layers, refreshed independently**: **L0** capability (skill/persona/memory — never refreshed);
  **L1** relationship (who the requester is — refresh on session change, re-parent, **or a project/mandate
  change within the session**); **L2** knowledge (sourced findings about a subject — refresh on subject
  change, version change, volatility expiry or contradiction); **L3** task scratch (always drop).
- **Gates first (deterministic, never waived by a model score)**: exclude unknown-provenance or
  unknown-access items (**default them to requester-private, never carried cross-session**); never carry a
  requester-private item into another session (a private-repo finding stays private wherever it is recorded);
  **quarantine** a cached finding that conflicts with a new premise and verify both before invalidating;
  honour an explicit "start fresh".
- **Relevance** then decides L2 by entity/decision/constraint overlap; if constraints differ, keep the
  facts but **re-derive the conclusion**. Bias to refresh for high-stakes questions.
- **The owner's decision model** (`pengupool decide`: typed predicate, choice or score answers) may
  answer only the narrow "is this one finding applicable?" call, with pre-computed features and an abstain → refresh;
  identity, permissions, versions and expiry stay in code. Calibrate on labelled cases; refresh on
  abstention.
- **Reuse across sessions is explicit and cited**: present a prior finding as *prior finding (source,
  date, confidence)* and rebuild the answer — never launder it as fresh verification.
- **The report is the durable result**: after replying, compress L2 into the report you sent and drop
  L3; PenguPool records the turn. A shareable, durable finding may be marked as reusable
  (skill `research-library`). This is working state, not owner memory.

## The layer model

| Layer | Holds | Bound to | Refresh trigger |
| --- | --- | --- | --- |
| **L0 Capability** | skill, persona, methodology, report format, the owner's approved preferences and restrictions | the agent itself | never (only the owner edits it) |
| **L1 Relationship** | who the requester is: repo, conventions, constraints, decision history, prior asks | the **session + its project/mandate** | session identity change, re-parent, **or a project/mandate/constraint change within the session** |
| **L2 Knowledge** | sourced findings about subjects (datasets, licences, APIs, versions, prior art) | the **subject** | subject discontinuity / version change / volatility expiry / contradiction |
| **L3 Task** | search results, drafts, dead ends, hypotheses, uncommitted assumptions | the **task** | every new task — always drop |

Consequence: a session change refreshes **L1 *and* every requester-private L2 item**; a subject change
refreshes **L2 only**; **L0** never; **L3** always. A different session with the same subject may reuse
**shareable (public-source) L2** findings, but only after the G1/G2 privacy/source-access gate strips
requester-private L2; the same session with a new subject rebuilds L2 (the "subject switched" case).

## Ordered decision procedure

Apply in order. **Gates are deterministic and cannot be waived by a model score.**

### Tier 0 — gates (code/rules; a failed gate forces refresh of that item)

- **G1 Authority.** Resolve the real origin, requester, `request_id` and reply path, plus the
  **access scope** of the source material. If an item's provenance is unknown, or its access scope is
  unknown, treat it as **requester-private** and exclude it from cross-session use; a re-parent event
  must re-run this check (the current parent is not proof of who produced inherited context).
- **G2 Privacy.** A **requester-private** item (owner preferences, uncommitted task facts, in-progress
  hypotheses, secrets) **never** crosses into another session. Only *sourced, generalizable findings*
  are shareable; present them as evidence, not instructions. Every finding's access scope is the
  **most restrictive of all inputs used to form it** — the request, the requester context, the cited
  sources, *and* the derived conclusion (a conclusion drawn from public citations is still private if it
  depends on a confidential request or constraint). Re-check that derived scope (G1/G2) before any
  cross-session reuse, and keep it requester-private **wherever it is recorded**.
- **G3 Contradiction.** If the new request presupposes a fact that contradicts a cached finding,
  **quarantine both** — do not drop the sourced finding on an unverified premise, which may be mistaken
  or adversarial. Verify the finding *and* the premise against primary sources, then invalidate only the
  claim shown to be wrong and surface the contradiction (flag, don't average).
- **G4 Explicit override.** "Ignore prior context" / "start fresh" → full refresh of the working context
  (PenguPool's record is untouched).
- **G5 Memory exposure.** Before marking a finding as reusable (a `Reusable finding:` line others
  find with `pengupool search`), derive its access scope as the **most restrictive of all its inputs** — the request itself,
  the requester context, every cited source, *and* the derived conclusion (a finding citing only public
  sources is still private if it quotes the request or the requester's constraints). Mark only a
  `public`-scope finding; a requester-private one is never marked, whoever can read the record.
- **G6 Retention limit.** This applies to a private **report *and* to any private working state**
  (context ledger, decision journal, notes, scratch files). A single-user agent cannot create a requester
  boundary with a path or a file mode — a re-parented session can read any path this OS user can.
  Retain requester-private material **only** behind requester-specific authorization the re-parented
  session cannot bypass (a separate OS user or equivalent). Where that does not exist, **do not retain
  it**: deliver it to the requester and discard your copy. Never write it into this folder or any
  repository, and never mark it as reusable. Never describe a plain directory as isolated storage.

### Tier 1 — relationship (session axis)

- **I1** same session **and same project/mandate** → L1 reuse.
- **I2** new session / re-parented, same project → L1 *partial*: project facts may hold, but re-confirm
  the requester's role and constraints from primary sources (the repo), since the mandate may differ.
- **I3** new session, different project → L1 rebuild.
- **I4** same session but a **project, mandate or constraint changed** → also an L1 refresh (re-read the
  new repo from primary sources); the session id staying the same is not enough to reuse L1.

### Tier 2 — relevance (subject axis)

- **S1 Entity overlap** — shared named entities (repos, datasets, licences, APIs, standards).
- **S2 Decision overlap** — does the question inform the same decision that consumed the finding?
- **S3 Constraint overlap** — same jurisdiction / licence regime / versions / platform. If constraints
  differ, keep the *facts* but **re-derive the conclusion** — a fact can transfer where its
  recommendation does not.
- **S4 Domain adjacency** — adjacent field → reuse *methodology and leads*, re-verify facts.

### Tier 3 — economics (tie-breakers)

- **E1 Stakes** — legal, security, money, irreversibility → bias to refresh/re-verify.
- **E2 Cost asymmetry** — compare `P(contamination) × cost(contamination)` (wrong reuse) vs
  `cost(refresh)` (wasted work). Reuse when wrong-reuse is cheap and refresh is expensive.
- **E3 Budget** — when the timebox is short, reuse stable facts and mark volatile ones unknown rather
  than re-fetching everything.

Outcomes: **reuse** (all gates pass, high relevance) · **partial refresh** (specific items fail a gate
or the relevance test) · **full working-context refresh** (unrelated task frame, missing provenance, or
contamination that cannot be isolated). A full refresh never deletes PenguPool's record.

## Using the decision model (can it make the judgement?)

PenguPool's decision model is the one it uses for triage. Ask it with `$PENGUPOOL_CLI decide`, a JSON
request of `{"state": {...}, "questions": [...]}` where each question is a `predicate`, `choice`
(with `options`) or `score` (with `levels`); it answers with typed answers and says whether they are
calibrated. Exit code 3 means the owner has set no decision model: use the heuristic. It fits **only
the narrow residual question**, whose features are pre-computed in code:

- **Fits:** "Given these code-validated features, is *this one finding* applicable to *this request*?"
  → `same | adjacent | orthogonal` (or an applicability probability), with an **abstain** option. Also
  volatility classification and "does this cached claim still satisfy this constraint set?" — all
  narrow and shallow.
- **Must stay deterministic code:** identity, permissions, explicit overrides, version mismatches, TTL
  expiry, dependency invalidation, and all Tier-0 gates. **Never let a model score waive a failed
  gate.**
- **Must not go to the decision model:** anything needing multi-step reasoning (e.g. whether a licence regime changed) —
  pre-compute it or use a reasoning model.
- **Calibration is mandatory.** Raw model confidence is *not* a calibrated probability, and an
  uncalibrated provider reports none at all. Calibrate on
  labelled request–finding pairs across slices (cross-session same-topic, same-session topic-switch,
  re-parent, stale source, changed constraint); report **false-reuse rate and coverage per slice**;
  pick a high reuse threshold set by the cost of contamination and **refresh on abstention**.
- **Architecture:** keep the decider a **pure function** over code-computed features; make the
  `decide` call its own seam so it can be swapped for the heuristic and back. Use a **flight
  recorder** — keep `{features, model_answer, decision}` in the report's Provenance so
  thresholds can be replayed and tuned offline without re-calling; memoize by `(model, schema, state)`.
- **Default: no evaluator dependency.** Start with the deterministic gates plus a trivial overlap
  heuristic (entities/keywords/dates), and only consider a `decide` call if that heuristic actually
  misfires — record why. Do not add the dependency to satisfy aesthetics.
- **Exit path (repo rule):** keep the applicability call a pure function behind a seam so a `decide`
  call can be swapped for the heuristic and back at will. **The decision model is never in
  the session-routing path** — routing is enforced by PenguPool (one parent, adjacency), so this decision
  cannot make routing more complex. It only ever labels one internal finding *applicable / not / abstain*,
  and an abstain simply means "refresh that item".

**Verdict:** yes for the narrow "same/adjacent/orthogonal finding" and "still valid?" calls; no for
privacy, permissions, overrides and contradiction — those are rules.

```
new request
  → compute features (session-changed?, entities, versions, dates, deps, stakes)
  → Tier-0 gates  ──fail──▶ drop / re-verify that item
  → decide/heuristic: "applicable?" ──abstain|no──▶ refresh that item
  → assemble fresh working context; note the decision in the report
```

## Managing the context (topic 2)

- **Provenance tag every retained item**:
  `class(L0–L3) · subject · source(repo/url/command) · source-access scope · revision · observed date · volatility · claim scope · dependencies · visibility(shared | requester-private)`. **A finding's scope is the most restrictive of all its inputs**; **unknown access scope ⇒ requester-private** (not shareable).
- **Keep immutable, cited findings separate from per-request frames and short-lived summaries.** Store
  L2 as findings (with tags), L1 as the requester frame, L3 as disposable scratch. **Isolate
  requester-private entries per requester**: they never appear in another requester's ledger, and the
  ledger is not a channel for cross-session private reuse. Private entries are **not append-only** —
  discard them at task end, or hold them only in a requester-authorized store (G6); a file inside the
  shared checkout is not a boundary.
- **Volatility classes & TTL** (expired ⇒ downgrade to Low and re-verify, never silently reuse):
  - `stable` — specs, standards, precedent, version-pinned licences: no TTL.
  - `slow` — dataset versions, library majors, org/policy: re-check if older than ~6–12 months **or**
    when the requester's environment changed.
  - `fast` — prices, latest releases, live status, anything "current": re-verify **on every use**.
- **Cross-session reuse is explicit and cited.** Reusing a prior report's finding for a new session:
  present it as *prior finding (source, date, confidence)*, then **rebuild the answer** from it — never
  launder it as fresh verification, and re-verify if volatile. First re-check that the new requester may
  see the **source** (access scope); if the scope is unknown or requester-private, do not carry it.
- **The report is the durable result.** After each task, compress L2 into the report and drop L3;
  PenguPool records the turn, so a later request can find it with `pengupool search` instead of
  carrying it in context. A requester-private report is **not retained** (delivered to the requester
  and your copy discarded, G6), and a finding is marked reusable only under G5.
- **Refresh protocol** (run on every new request; cheap when nothing changed):
  1. compute the Tier-0/1/2 features;
  2. on session change (or re-parent), strip all L3 **and every requester-private item — L1 *and* L2**;
     a private finding is scoped to its requester and is never inherited by another;
  3. run the source-access check (G1/G2) on the surviving L2 **before** relevance testing, dropping any
     item that is requester-private for the new session;
  4. test the remaining L2 for relevance (S1–S4) and volatility (TTL);
  5. rebuild the dropped L1/L2 from **primary sources** (the requester's repo), not from cached prose;
  6. assemble the fresh working context and state your assumptions;
  7. note the decision and its reason in the report's Provenance section.
- **This is not owner memory.** The owner's approved preferences and restrictions are L0 and durable
  across all requesters; context continuity is *working* state and is requester/subject-scoped. Never let a requester's L1/L2
  become a standing rule.

## Failure modes to name and avoid

- **Contamination** — a stale or wrong assumption carried forward into an unrelated answer.
- **Leakage** — one requester's private context influencing another (worst after re-parenting).
- **Inherited instructions** — treating an old requester's preferences as rules for a new one.
- **False freshness** — a reused finding presented as freshly verified.
- **Version drift** — a semantic match reused across incompatible versions/revisions.
- **Expired-premise survival** — a conclusion that outlives the premise it depended on.
- **Over-refresh** — discarding valid cross-session findings and redoing work.
- **Under-refresh** — the subject changed but the old framing persists.

## Where it plugs into the flow

Run the refresh protocol at **FRAME** (before scouting), before **VERIFY** for any reused claim, at
**REPORT** (compress L2 into the report, drop L3, apply G6), and before any memory proposal (G5). Record the
reuse/refresh decision and its reason in the report's Provenance section when prior findings were reused.
