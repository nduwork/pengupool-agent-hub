# review-guide

A read-only peer review of a pull request. One stdlib-only script, `scripts/preflight.py`, does the
filtering and the GitHub reads, and the skills drive it, so any agent that can run a command can
use it. The helper's own guide is `AGENTS.md`.

**What it does**

- **`peer-review`** is the primary mode. It pins base and head, traces every reader of the state the
  change writes, checks the PR description's claims against the code, runs the documented checks,
  reproduces each blocker (or proves it statically and says so), and tries to disprove it before
  reporting. Findings are tagged new or pre-existing. The outcome ("no blocking findings" or "N
  blocking findings") is separate from severity and never says "merge-ready"; CI is reported
  separately. Re-review covers only the delta, in at most 3 rounds. It never edits, comments,
  approves, merges or pushes.
- The main workflow is one file; the optional steps are separate skills loaded only when the
  scenario applies: `peer-review-subagents`, `peer-review-rereview`, `peer-review-multi-pr`.
- **`review-guide-flowchart`** (optional, author-side) authors a Mermaid flowchart of what a change
  does into an owned section of the PR description; the diff it diagrams is secret- and PII-filtered
  first. It writes to the PR, so the peer review never loads it. `preflight.py check <pr>` says
  whether the section is current.
- **`review-guide-adversarial-review`** is an option the peer review calls for a risky PR: an
  independent reviewer attacks the approach and the assumptions.
- Nothing fires on its own: the review runs when asked.
- **Execution is the user's choice**: `REVIEW_GUIDE_EXECUTION=own | subagents[:N]` (default 3
  cheap read-only subagents) and `REVIEW_GUIDE_MODEL` (default: the cheapest capable model).
  `preflight.py execution` prints the result. Subagents get only the filtered input.

## Layout

```
pr-review-agent/
├── AGENTS.md             # the helper's guide
├── skills/
│   ├── peer-review/            SKILL.md: the whole main workflow
│   ├── peer-review-subagents/  SKILL.md: split work, filtered input, verifier (load when subagents)
│   ├── peer-review-rereview/   SKILL.md: delta-only, 3 rounds (load on new commits)
│   ├── peer-review-multi-pr/   SKILL.md: trial merge (load when several PRs are open)
│   ├── review-guide-flowchart/ SKILL.md + references/graph-format.md (optional, author-side)
│   └── review-guide-adversarial-review/  SKILL.md (option for risky PRs)
├── scripts/
│   └── preflight.py      # stdlib-only Python: config, excludes, redaction, GitHub reads
├── tests/
│   └── test_preflight.py # pytest
```

Skills reference the script relative to themselves (`../../scripts/preflight.py`).

## Per-repo config and opt-out

In the repo you're preparing a PR for, an optional `.github/review-guide.yml`:

```yaml
enabled: true        # false turns review-guide off for this repo
adversarial_review: false  # opt in to the independent adversarial review step
adversarial_reviewer: ""   # optional reviewer command; {base} becomes origin/<base>
direction: LR        # flowchart direction, or TD
max_nodes: 25        # flowchart size, capped at 40
exclude:             # added to the built-in secret/data excludes
  - "generated/"
  - "tests/fixtures/"
```

Set `REVIEW_GUIDE_DISABLE=1` to turn it off everywhere, or `enabled: false` per repo. The peer
review writes nothing to a PR and nothing here blocks a push or a merge. The keys of the retired
self-check, merge guard and second-opinion steps (`self_check`, `merge_guard`, `second_opinion`) are
ignored.

## Retired steps

The self-check, the second opinion and the flowchart merge guard left this helper. The self-check's
simplification pass is `simplify-change` in dev-workflow-agent; the unslop prose pass and the second
opinion (which sent the change to an external model) were removed. The flowchart stays, as an
optional author-side skill.

## Maintaining this package

### Naming

User-facing names stay `review-guide`: the per-repo config is `.github/review-guide.yml`, the
opt-out env var is `REVIEW_GUIDE_DISABLE=1`, and the execution settings are
`REVIEW_GUIDE_EXECUTION` and `REVIEW_GUIDE_MODEL`.

### Conventions

- Skill frontmatter is `name` + `description` (lead with WHEN) + optional `triggers`. Directory
  name matches `name:`.
- Skills reference the bundled script relative to themselves: from `skills/<skill>/SKILL.md` the
  script is `../../scripts/preflight.py`.
- Change `peer-review`, then replay a few PRs with known bugs by hand before the PR.

### Checks

```bash
python3 -m pytest tests -q          # preflight.py
```

### Gotchas

- **`preflight.py` runs under `python3` and is stdlib-only.** Callers pass arguments, never a shell
  string, so paths never go through a shell. Keep it that way.
- **Never commit secrets, credentials, or PII.** The script redacts secret/PII-shaped values by
  design; don't bypass the filter, and don't hand a subagent anything it did not print.
- **Only `apply` writes** (the flowchart skill, over stdin to the PR body). The peer review never calls it.

## License

MIT.
