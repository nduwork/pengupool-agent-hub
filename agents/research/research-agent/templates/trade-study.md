# Trade study (engineering decision)

Use for choosing between 2–3 real options (a library, datastore, algorithm, protocol, workflow
shape, or datasource). Narrow to 2–3 candidates; a study with one option is not a study.
Based on Microsoft's trade-study template
(<https://microsoft.github.io/code-with-engineering-playbook/design/design-reviews/trade-studies/template/>)
with weighted scoring.

```markdown
# Trade study: <decision>

- **Request**: <id / one line>   **Requester**: <session>
- **Date**: <YYYY-MM-DD>   **Effort tier**: quick scan | standard | deep dive
- **Decision to make**: <one line>
- **Decision drivers**: <the 1–3 constraints/criteria that actually matter>

## Problem & assumptions
<What must the solution do? Assumptions about the rest of the system; inputs/outputs.>

## Constraints (eliminators — apply before scoring)
- Team/skills: …
- Deadline / budget: …
- Stack / existing systems / backwards compatibility: …
- Legal, licence, data residency, security: …
- Operational maturity required: …

## Options
### Option A — <name>
<What it is; why it could win.>
### Option B — <name>
…
### Option C — <name>
…
### Rejected before scoring
- <option> — <constraint that eliminated it>

## Criteria & weights
| Criterion | Weight | How measured |
| --- | --- | --- |
| Fit / capability | 5 | testable scenario |
| Operability / complexity | 4 | … |
| Cost (build + run) | 3 | … |
| Risk / reversibility | 3 | … |
| Licence / support | 2 | … |

## Scores
| Criterion | W | A | B | C | Notes |
| --- | :-: | :-: | :-: | :-: | --- |
| Fit | 5 | 4→20 | 3→15 | 2→10 | |
| Operability | 4 | 3→12 | 4→16 | 2→8 | |
| Cost | 3 | 2→6 | 3→9 | 5→15 | |
| Risk | 3 | 3→9 | 2→6 | 2→6 | |
| Licence | 2 | 5→10 | 5→10 | 3→6 | |
| **Weighted total** | | **57** | **56** | **45** | |

## Recommendation
<Winner + one paragraph. State the weights that drove it and what would re-rank the options.>

## What would change this
- <e.g. if scale becomes the binding constraint; if the team grows; if the licence fails legal review>

## Proof / next step
<Cheapest experiment that de-risks the choice, and what it must show.>

## Provenance
<Commands, files, URLs (accessed <date>).>
```

## Rules
- **Weights encode the decision.** Re-weighting for a different system can flip the winner; say so.
- **Constraints eliminate.** If a constraint disqualifies the top scorer, take the next survivor —
  do not score around it.
- **Anti-patterns**: resume-driven (CV-driven), hype/cargo-cult ("Netflix does it"), maximizing
  every attribute, premature distribution. Prefer the boring option that fits.
- **Record the decision** as an ADR when it lands.
