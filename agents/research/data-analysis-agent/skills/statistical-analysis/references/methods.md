# Methods, formulas and code

Inputs below are aggregates unless marked "unit-level". Python snippets need `scipy` /
`statsmodels`; without them, the formulas run in SQL or plain Python.

## Proportions

Inputs per group: successes `x`, trials `n`.

- Rate `p = x / n`. Wilson 95% interval (good at small n and near 0 or 1):
  centre `(p + z²/2n) / (1 + z²/n)`, half-width `z·sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n)`, `z = 1.96`.
- Difference `p1 − p2` with a Newcombe interval, or the simple Wald interval
  `± 1.96·sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)` when every `x` and `n − x` is comfortably above 10.
- Relative risk `p1/p2`, odds ratio `(x1/(n1−x1)) / (x2/(n2−x2))`; intervals on the log scale.

```python
from statsmodels.stats.proportion import proportion_confint, confint_proportions_2indep, test_proportions_2indep
proportion_confint(x, n, method="wilson")
confint_proportions_2indep(x1, n1, x2, n2, method="newcomb")      # difference p1 - p2
test_proportions_2indep(x1, n1, x2, n2)                            # z-test
from scipy.stats import fisher_exact; fisher_exact([[x1, n1-x1], [x2, n2-x2]])
```

## Means

Inputs per group: `n`, mean `m`, standard deviation `s` (all from SQL `COUNT`, `AVG`, `STDDEV`).

- Welch: `se = sqrt(s1²/n1 + s2²/n2)`, `t = (m1 − m2) / se`; degrees of freedom by the
  Welch-Satterthwaite formula. Interval `(m1 − m2) ± t_crit·se`.
- Cohen's d: `(m1 − m2) / sqrt(((n1−1)s1² + (n2−1)s2²) / (n1 + n2 − 2))`.

```python
from scipy.stats import ttest_ind_from_stats
ttest_ind_from_stats(m1, s1, n1, m2, s2, n2, equal_var=False)
```

Skewed outcomes (turnaround times, costs): compare medians or log-transformed means, or bootstrap
(unit-level, run without printing data):

```python
import numpy as np
rng = np.random.default_rng(0)
diffs = [np.median(rng.choice(a, a.size)) - np.median(rng.choice(b, b.size)) for _ in range(5000)]
np.percentile(diffs, [2.5, 97.5])
```

## Categorical association

Input: a contingency table of counts (suppress cells < 10 before reporting it, not before testing).

```python
from scipy.stats import chi2_contingency
chi2, p, dof, expected = chi2_contingency(table)
cramers_v = (chi2 / (table.sum() * (min(table.shape) - 1))) ** 0.5
```

Expected counts below 5 in more than a fifth of cells: merge categories or use an exact test.

## Several groups and many tests

- Welch ANOVA / Kruskal-Wallis for "any difference"; then pairwise comparisons with Holm
  correction.
- Many metrics or segments: `statsmodels.stats.multitest.multipletests(pvals, method="holm")`, or
  `"fdr_bh"` when screening.

## Regression (unit-level, in place)

```python
import statsmodels.formula.api as smf
fit = smf.logit("outcome ~ group + age_band + site", data=df).fit()   # df holds no identifiers
fit.params, fit.conf_int()                                             # report these, not df
```

Use bands (age band, month) rather than exact personal values as covariates. Check residuals,
influential points (Cook's distance as a count above threshold) and collinearity (VIF). Report
coefficients as effects in outcome units or odds ratios with intervals.

## Rates over time

- Poisson rate ratio for events per exposure (per day, per 1,000 tests); check overdispersion
  (variance ≫ mean → negative binomial).
- Trend: compare year over year to remove seasonality; a 7- or 28-period moving average to see
  direction; a regression on time with seasonal terms when a slope is needed.
- Anomaly: expected value from a moving average or the same period last year; flag residuals
  beyond about 3 robust SDs (median absolute deviation × 1.4826). Separate one-off spikes from a
  step change (level shift that persists).

## Outliers

- IQR fences: below `Q1 − 1.5·IQR` or above `Q3 + 1.5·IQR`; z-score > 3 only for roughly normal
  data; percentile caps (p1/p99) for a quick view.
- Report the count above each fence and the result with and without them. Errors (impossible
  values) are a validation issue; real extremes are kept and handled with robust statistics.

## Sample size and power

Two proportions, 80% power, alpha 0.05, roughly: `n per group ≈ 16·p(1−p) / δ²` for a difference
`δ` around rate `p`. Two means: `n per group ≈ 16·s² / δ²`.

```python
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_effectsize
NormalIndPower().solve_power(effect_size=proportion_effectsize(p1, p2), alpha=0.05, power=0.8)
TTestIndPower().solve_power(effect_size=d, alpha=0.05, power=0.8)
```

For a null result, state the smallest effect the sample could detect with 80% power.

## Plain-language phrasing

| Result | Say |
| --- | --- |
| CI excludes 0, effect meaningful | "B is higher by about X (likely between L and U)." |
| CI excludes 0, effect tiny | "There is a difference, but at about X it is too small to matter for this decision." |
| CI includes 0, wide | "We can't tell: the data fit anything from L to U. We'd need about N per group to settle it." |
| CI includes 0, narrow | "No meaningful difference: any effect is most likely between L and U." |
| Observational data | add "This is an association; <confounder> could explain part of it." |
