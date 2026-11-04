# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org).

## [Unreleased]

### Changed

- **PenguPool memory model: nothing is written into this folder.** Lookups use
  `pengupool memory search`; the owner's preferences and restrictions are proposed with
  `pengupool memory propose --kind preference|restriction` (owner's own words only); reusable findings
  with `--kind fact` (skill `research-library`, never-ask-twice via `memory search`). Reports go back
  to the requester; the host records every turn. `AGENTS.md`, both skills, README, docs and templates
  updated; `LIBRARY.md` and `logs/` are now a read-only archive.

### Removed

- The memory and library editors and their tests, `docs/memory.md`, `docs/library.md`, the memory
  and library-entry templates, `references/session-memory.md`, `references/library-format.md`, and
  the memory/lock entries in `.gitignore`.

## [0.5.0] - 2026-10-13

### Changed

- **One history store: the `research/` archive is gone.** Per-subject logs under `logs/` now carry the
  findings inside their dated entries (`## YYYY-MM-DD · session · <slug>`, report body under
  `### Report —`), which is the skill-repo layout. The 37 per-task logs and 24 reports were folded into
  8 subject logs with no content loss; `logs/INDEX.md` is now `Subject | Log | Started | Last updated`.
  `LIBRARY.md` entries point at `logs/<subject>.md#<entry-slug>`; `library.py` gained a `retarget`
  command for exactly that move (repoints the item, refreshes the fingerprint and the file's header).
  AGENTS.md rules 4/5/7, README, docs, both skills, templates and tests were updated with it.

## [0.4.0] - 2026-10-12

### Changed

- **Not-retained delivery records share one subject log**, `logs/not-retained-deliveries.md` (one dated
  section per delivery, one `INDEX.md` row updated in place). AGENTS rule 5, the research-agent skill's archive
  step, `docs/design.md` and `context-continuity.md` say so; the 11 per-report files were merged. Reviewed by a
  separate review agent (findings fixed).

- **Task history consolidated into `logs/`** (skill-repo layout): one `logs/YYYY-MM-DD-<slug>.md` per
  finished task + `logs/INDEX.md`, backfilled from `research/INDEX.md` (retired), `git log`, `.step-status/`
  and `.pi/codex/` review logs. `CHANGELOG.md` now records agent releases only; reports are listed in the log.

## [0.3.0] - 2026-09-28

### Added

- **Research archive growth** (all `public` scope, indexed in `research/INDEX.md`):
  - `research/2026-09-28-brave-search-api.md` — Brave **Web Search** API guide (plans/gating, correct
    request + parameters, exact rate-limit header semantics incl. `0` = unlimited, error-code branching,
    fail-closed handling, agency-news recommendation).
  - `research/2026-09-28-brave-answers-api.md` — Brave **Answers** surface (endpoint, models
    `brave-pro`/`brave`, structured `<citation>` JSON with `url` requiring `stream=true` +
    `enable_citations=true`, cost formula, limits).
  - `research/2026-09-28-litellm-briefing.md` — LiteLLM LLM gateway + SDK (MIT core, routing, proxy,
    licence/maintenance/exit-path assessment).
- **First `LIBRARY.md` entry**: `litellm-gateway` — indexes `research/2026-09-28-litellm-briefing.md`
  (the library is a curated index of reusable `research/` items).

## [0.2.0] - 2026-09-27

### Added

- **Reusable research library** (`LIBRARY.md`, `docs/library.md`, skill `skills/research-library/`): a
  committed, owner-approved **index of items in `research/`** that are worth reusing on other projects —
  it points at those reports and does not copy them. The `research-library` skill defines when to offer a
  candidate (*shareable · generalizable · durable · non-obvious · not already decided*), the **ask-once**
  ritual (an **atomic, opaque reservation** — slug + item fingerprint, no title — taken *before* asking,
  so parallel sessions never ask twice), and the anti-re-ask check across entries, declines and
  reservations. The editor `skills/research-library/scripts/library.py` provides lock + compare-and-swap
  + post-write verification and refuses duplicate keys, a duplicate item (same `research/` path under an
  alias key), an omitted/non-`public` scope, an item outside `research/`, multi-line/marker-bearing
  fields (record-forgery guard), and free-form decline text (declines store only slug + fingerprint); an
  explicit **`release`** (coordination token, or `--force` for an abandoned reservation) drops/redos a
  reservation on edit or after an interrupted session; `apply` requires the reservation token. The token
  is a coordination aid only, not a security boundary (single-user filesystem). Schema
  `templates/library-entry.md`; tests `tests/test_library.py`. Wired into `AGENTS.md` and the
  `research-agent` task-start (read + reuse) and task-end (offer) rituals.
- **Context continuity** (`skills/research-agent/references/context-continuity.md`): how to decide
  reuse vs partial vs full refresh when the requesting session changes, this session is re-parented, or
  the same session starts a different subject. A four-layer model (L0 capability, L1 relationship, L2
  knowledge, L3 task scratch), deterministic gates (authority, privacy, contradiction, explicit
  override), relevance tests, and economics tie-breakers. Analyses a **Jev**-style typed single-pass
  evaluator for the narrow "is this finding applicable?" call (with abstain → refresh, code-owned
  identity/permission/version/TTL, and mandatory calibration), plus provenance tagging with a
  **source-access scope** (a private-repo finding stays private even after archiving), volatility/TTL
  decay, and safe cross-session reuse rules. Contradictions quarantine and verify both sides before
  invalidating, and the ARCHIVE step gains an **access-scope gate** (G5): a requester-private report is
  committed to the shared archive only when **verified effective-reader parity** with its source holds
  (owners + collaborators + any published site, not ownership alone), otherwise the agent **does not retain
  it** — it delivers the report to the requester and discards its copy, and the index carries only a
  detail-light pointer (a path or file mode is not a requester boundary). G6 covers a private **report and
  any private working state** (context ledger, journal, notes); a not-retained report is delivered **in
  full** through the verified reply path before the agent's copy is discarded.
- **Retention rule (G6)**: the four pending requester-private reports were delivered to the requester and
  the agent's copies were **removed**; `research/INDEX.md` keeps only detail-free pointers. Gitignore is
  documented as accidental-commit protection only, never as access control.
- **Context-ledger template** (`templates/context-ledger.md`) for the requester frame, tagged findings
  and the reuse/refresh decision journal.
- **Memory editor: in-place `update`** (`skills/research-agent/scripts/memory.py`): the proposal may now
  carry `update` (a map of entry id → new line), which replaces a single existing entry verbatim under
  the same lock + compare-and-swap, refusing a missing or ambiguous id. This lets an entry be corrected
  or marked superseded without a plain-text write or a full-file rewrite; `tests/test_memory.py` covers
  it.
- **Skill + contract wiring**: a "Context continuity" section in `SKILL.md` (and the FRAME/ARCHIVE
  steps), and a "Context continuity (reuse vs refresh)" subsection in `docs/design.md`.

## [0.1.0] - 2026-09-27

### Added

- **Research-agent contract** (`docs/design.md`): frame → scout → plan → gather → verify → converge →
  report → archive, with per-claim source + confidence and a definition of done.
- **Engineering-scout persona** (`docs/persona.md`): divergent prior-art search, then a convergent,
  constraint-led recommendation; a brainstorming mode.
- **Landscape survey** (`docs/survey.md`): how existing deep-research and coding agents are built,
  plus the engineering discovery tooling worth using.
- **PenguPool orchestration findings** (`docs/orchestration.md`): how routing works and four ways to
  summon the agent (@tag, re-parent, spawn-per-request, route-to-hub).
- **pi skill** `skills/research-agent/` with methodology and report-format references.
- **Templates**: research request, findings report, and a weighted trade study.
- **Owner memory** (`docs/memory.md`, `AGENTS.md`): a gitignored `MEMORY.md` for the owner's durable
  preferences, restrictions and deferred ideas; read at task start, captured at task end only after
  the owner confirms, with provenance rules and a lock + compare-and-swap editor
  (`skills/research-agent/scripts/memory.py`).
- **Tests**: stdlib `unittest` smoke tests for the memory editor (`tests/test_memory.py`).
- **pi package manifest** (`package.json`), and the staged setup plan (`docs/plan.md`).
