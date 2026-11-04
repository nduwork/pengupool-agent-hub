# Scoping framework — prompts and checks

## Sharpening an idea

- Can it be said in one sentence a colleague outside the field would follow? If not, it is
  probably two projects.
- What is new: the question, the system, the method, or the data? One new thing is usually
  enough; four is usually too many.
- Make it more general: does the finding apply beyond this organism, tissue or disease?
- Make it more feasible: is there a simpler system, an existing dataset, or a proxy readout?
- Look for ideas at the edges: a new measurement method that makes an old question answerable,
  a dataset collected for one purpose that answers another, a result in one field that has not
  reached the next.
- Watch for ideas chosen because they are easy, fashionable, or a small step from the last
  paper, with no answer to "why would anyone care".

## Assumption table

| # | Assumption | Biology or method | Risk 1–5 | Months to know | Depends on |
| --- | --- | --- | --- | --- | --- |

Risk scale: 1 very likely (> 90%), 2 likely, 3 uncertain (roughly a coin flip), 4 unlikely,
5 very unlikely (< 10%). Try to argue each one is false; if you cannot, the score is low.

Questions that find hidden assumptions:
- What must be true about the biology for the effect to exist?
- Is the effect large enough to detect with the samples you can get?
- Can the method measure it in this system (sensitivity, throughput, cell type access)?
- Can the analysis separate signal from batch, donor and technical noise?
- If it works, how will it be validated independently?
- Will the result be interpretable either way? A design where only a positive result is
  informative is a risk in itself.

Profiles to fix before starting:
- A score-4 or 5 assumption that reads out after a year or more: find an earlier proxy test.
- More than two assumptions at 4–5: shrink the project or split it.
- Risky assumptions in a chain: test the first one alone before building on it.
- Everything at 1–2: probably incremental; look for a way to raise impact.

## Data feasibility checklist

- Source: in-house cohort, collaborator, public repository (GEO, SRA, ENA, cellxgene, consortium
  portals), or new collection.
- Permissions: consent covers this use; controlled access approved; data can be processed where
  it is needed. No identifiable data leaves its approved environment.
- Size: number of independent units (donors, animals, cultures), not cells or reads. A rough
  power estimate from a pilot or published effect sizes.
- Design: conditions spread across batches; controls present; covariates (sex, age, site)
  recorded.
- Quality: platform, depth, QC summaries; missing metadata that would block the analysis.
- Cost and time: compute, sequencing, sample access lead times.

## Choosing the constraint to fix

List the parameters: organism or system, cell type or tissue, method, specific question,
application. Signs of too many fixed: every change breaks the plan, no fallback exists. Signs of
too few: months pass without a decision on what to measure. Fix the one that carries the
project's value (the question, or the unique sample set, or the new method) and keep at least
two others open.

## Decisive first experiment

A good one:
- tests the highest-risk, earliest-reading assumption;
- takes weeks and a small budget, or reuses data already in hand;
- has a readout and thresholds written down before it runs;
- changes what you do next whichever way it comes out.

Template: "If <readout> shows <result> by <date>, we continue with <next step>; if it shows
<other result>, we <stop / switch to alternative>."

## Decision points during the project

Alternate between doing the work and stepping back to judge it as if someone else had done it.
At each review: what did we learn, what changed outside the project, is the original plan still
the best path, what are three alternatives. A plan from a year ago is rarely still the best one.

## Rescue moves

| Situation | Move |
| --- | --- |
| Routine technical block | Let one fixed parameter vary: a different system, method or cell type that tests the same idea |
| Original goal unreachable | Pick a different goal of comparable value that the work so far can reach |
| Results answer another question | Name that question; decide whether it is worth more than the original |
| Repeated failures at one step | Stop and ask whether the step is necessary at all |

Treat a crisis as a chance to fix the problem and improve the project at the same time.

## Brief template

1. Question (one sentence) and kind of project.
2. Why it matters: the impact axes and who benefits.
3. Assumption table, ranked.
4. Data and sample plan, permissions and gaps (cohort size and type only).
5. Fixed constraint and what stays open.
6. First experiment with go/no-go criteria and date.
7. Next decision points.
8. Open questions and unverified claims.
