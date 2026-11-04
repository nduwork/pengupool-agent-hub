---
name: statistical-analysis
description: Chooses and runs a sound statistical method for a data question — descriptive summaries, group comparisons, tests of proportions and means, regression, trends, anomalies and intervals — checks its assumptions, reports effect sizes with confidence intervals, guards against common traps, and explains the result in plain language. Use when comparing groups, asking whether a change is real, describing a distribution, finding outliers, or modelling a relationship.
triggers:
  - is this difference significant
  - compare groups
  - a/b test
  - confidence interval
  - statistical test
  - is this trend real
  - outliers
  - regression
---

# Statistical analysis

Pick the simplest method that answers the question, check that it fits the data, and report how
big the effect is and how sure we are. Method table, formulas and code:
[references/methods.md](references/methods.md).

## Privacy in analysis

- Pull **aggregates** into the analysis whenever the method allows: counts and successes per
  group (proportions, chi-square), n / mean / variance per group (t-tests, ANOVA), binned
  histograms or quantiles (distributions).
- When a method truly needs unit-level values (regression, Mann-Whitney, bootstrap), run it inside
  the database or a local script that never prints rows; drop identifier and personal columns
  before loading, and output only coefficients, statistics and intervals.
- Outliers and anomalies are reported as counts, thresholds and the periods or segments they fall
  in, never as a list of records.
- Suppress any group with fewer than 10 units in reported tables and charts.

## 1. Frame it

- What decision does the answer feed? That sets the effect size that matters.
- Describe, compare, explain, or forecast? Each needs a different tool.
- What is the unit (patient, sample, order, day)? Units must be independent for most tests;
  repeated measures on the same unit need a paired or clustered method.
- Was there randomisation? Without it, a difference is an association; say so.

## 2. Describe first

Before any test, show for each group: n, mean and median, spread (SD or IQR), key percentiles,
the share of zeros/missing, and the shape (skew, long tail, two humps, floor or ceiling). If mean
and median disagree, lead with the median or a percentile summary. Plot or bin the distribution
before choosing a test.

## 3. Choose the method

| Question | Default | When assumptions fail |
| --- | --- | --- |
| Two proportions (rates) | difference with Wilson/Newcombe interval; two-proportion z-test | Fisher's exact when expected counts are small |
| Two means | Welch's t-test and interval | Mann-Whitney or a bootstrap interval for skewed data |
| Before/after on the same units | paired t / difference interval | Wilcoxon signed-rank |
| Three or more groups | Welch ANOVA, then pairwise with correction | Kruskal-Wallis |
| Two categorical variables | chi-square test, Cramér's V | Fisher's exact for sparse tables |
| Relationship between numbers | Spearman (robust) and Pearson; scatter | — |
| Effect adjusted for other factors | linear or logistic regression | robust errors; transform the outcome |
| Counts per period | Poisson rate ratio | negative binomial if overdispersed |
| Time to an event | Kaplan-Meier, log-rank, Cox | — |
| Trend over time | moving average + year-over-year; regression on time | seasonal decomposition |

Prefer intervals to bare tests. Fix the method and the alpha before looking at the outcome.

## 4. Check assumptions

Independence of units, adequate n (rule of thumb: ≥ 10 successes and failures per group for
proportion intervals; for means, skew matters more than n), similar variance or use Welch,
linearity and residuals for regression, no leakage between groups. When an assumption fails, use
the fallback column above and say so.

## 5. Report

- **Effect size** in the outcome's own units (percentage points, hours, ratio), with a 95%
  confidence interval. Add a standardised size (Cohen's d, odds ratio, Cramér's V) when units are
  not intuitive.
- **The test** and its p-value, as supporting evidence, not the headline.
- **Practical meaning**: is the interval inside or outside the size that would change the
  decision? "Real but too small to matter" is a valid result.
- **Power** when the result is null: what effect could this sample have detected?
- **Plain language**, one or two sentences a non-statistician can act on, with rounded numbers.

Example: "Turnaround was 6.1 hours shorter at site B (95% CI 3.8 to 8.4; Welch t-test,
p < 0.001, n = 1,240 and 980). That is large enough to matter; it is an observed difference, not
proof that site B's process causes it."

## Traps

- **Many looks**: testing many segments or metrics finds "winners" by chance. Count the tests,
  correct (Holm or Benjamini-Hochberg), or label the result exploratory.
- **Peeking**: stopping an experiment when p dips below 0.05 inflates false positives.
- **Correlation as cause**: name the plausible confounders and the direction question.
- **Simpson's paradox**: check the effect inside key segments, not just in the total.
- **Regression to the mean**: units picked for being extreme drift back without any treatment.
- **Ecological inference**: group-level patterns do not describe individuals.
- **False precision**: report 2–3 significant figures and a range, not "4.731%".
- **Outliers**: investigate before removing; report what was excluded and the result with and
  without.
