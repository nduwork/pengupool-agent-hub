# Methodology

## Source hierarchy

1. **The requester's own repo, config, or runtime output** — most authoritative for "how does *our*
   system behave". Give the exact command and its output.
2. **Primary upstream sources** — official docs, specifications/RFCs, changelogs, and source code
   read at a pinned version/tag. Quote the version.
3. **High-quality secondary write-ups** — reputable engineering blogs, peer-reviewed papers. Use
   for orientation, verify against tier 1–2.
4. **Forums, Stack Overflow, AI answers** — **leads only**. Use them to find a primary source; never
   cite them as evidence.

## Engineering sources (use before broad web prose)

| Need | Tool / source |
| --- | --- |
| Our system's behaviour | the repo, config, tests; run it, read it |
| How a library/API behaves | primary docs + source at a pinned version; a tiny reproduction |
| Prior art / implementations | GitHub code search, **grep.app**, Sourcegraph Deep Search, **Exa code** (`exa-code`) |
| Package truth (versions, deps, advisories) | **deps.dev** API, registry APIs (npm/PyPI/crates/Maven/NuGet/RubyGems/Go), libraries.io |
| Algorithms / methods | arXiv, Semantic Scholar, **Papers with Code** (benchmarks + leaderboards) |
| Benchmarks to anchor a claim | GAIA, BrowseComp, HLE/GPQA (QA); DeepResearch Bench (RACE/FACT), FreshWiki (reports); SWE-bench / Multi-SWE-bench (code) |
| Licence / maintenance / exit path | repo licence + release/commit cadence + open-issue health; the registry page |

Protocols: **MCP** for tool access, **A2A** for agent collaboration — keep output structured and portable.

## Verification by reproduction (engineering ACI habits)

- **Show the command and its raw output.** A paraphrase of output is not evidence.
- **Prefer the cheapest reproduction** that decides the claim: a 10-line script, a pinned doc, a
  one-line `curl`, a minimal test.
- When a search returns nothing, say "no results" explicitly — do not imply absence of evidence is
  evidence of absence.
- For benchmarks, check the **methodology matches our workload** before quoting a number
  (dataset, hardware, units, version).
- For a library choice, always check **licence, recent activity, and an exit path** before recommending.

## The gather loop

`THINK → SEARCH → READ → (reflect) → THINK …`

- **THINK**: what do I still need, and what is the cheapest evidence that would settle it?
- **SEARCH**: one question per query; vary phrasing if the first pass is empty.
- **READ**: open the source; extract and record the claim it supports immediately.
- **Reflect**: are there gaps or contradictions? If yes, loop; if the marginal value is low or the
  timebox is near, stop and mark the remainder unknown.

## Verification

| Claim type | How to verify |
| --- | --- |
| Local behaviour | Run the command / read the code at a pinned revision; paste output. |
| API/library behaviour | Primary docs at a pinned version; ideally a tiny reproduction. |
| Datasource facts | Primary provider docs/terms; check access method and licence directly. |
| Fast-moving facts | Check the publish/update date; state the access date. |
| Numbers/benchmarks | Confirm the methodology matches the question; do not compare unlike units. |

Cross-check any factual claim against **two independent primary sources** where feasible. If they
disagree, report both and the reason, rather than a blended average.

## Confidence labels

- **High** — primary source and reproduced locally, or two independent primary sources agree.
- **Medium** — one primary source, or strong secondary sources agreeing; not reproduced.
- **Low** — inference or a single weak source; state what would raise it.

Label the confidence of **each key claim**, not just the report. Never present an inference as a
fact. If the honest answer is "unknown", write that.

## Timeboxing

Decide the budget at FRAME. At ~70% of it, stop widening the search and start synthesizing. If the
evidence bar is unmet, deliver `PARTIAL`: what is known, what is not, and what would settle it.

## Housekeeping

- Keep a running "claims" list with a source beside each; promote it into the report.
- Keep raw notes and output out of every repository and this folder; only the distilled finding goes
  into the report.
- Record provenance (commands, URLs, access dates) in the report's Provenance section.
