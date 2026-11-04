# Landscape survey: existing research agents and how they are designed

Surveyed on 2026-09-27 from public sources (linked inline). Purpose: borrow the best patterns for
an **engineering** research agent — infra / algorithms / workflow / coding solutions — without
tying it to one research domain.

## 1. The two grand architectures

Almost every system is a point on two axes (taxonomy from *Deep Research Agents: A Systematic
Examination and Roadmap*, <https://arxiv.org/html/2506.18096v2>):

- **Static workflow (pipeline) vs dynamic agent.** Pipelines fix the control flow and let the LLM
  do each stage (deterministic, cheap, debuggable). Agents let the LLM choose the next action from
  feedback (flexible, expensive, non-deterministic). Anthropic's *Building effective agents* frames
  the same split and advises starting with the simplest pattern
  (<https://www.anthropic.com/engineering/building-effective-agents>).
- **Single-agent vs multi-agent.** Multi-agent helps when work is parallelizable and exceeds one
  context window; it hurts when agents must share context or are tightly coupled (same Anthropic post).

Anthropic's Research feature is the reference **orchestrator-worker**: a LeadResearcher plans and
spawns parallel subagents, each with its own context window; a CitationAgent attaches sources before
return. Findings that generalize (`https://www.anthropic.com/engineering/multi-agent-research-system`):

- Token usage explained **80% of performance variance** on BrowseComp; multi-agent ≈ **15× chat tokens**.
- **Scale effort to complexity** (1 agent / 3–10 tool calls for simple facts; 2–4 subagents /
  10–15 calls each to compare; >10 subagents for complex).
- **Delegate with a full brief**: objective + output format + tools/sources + boundaries.
- **Start wide, then narrow**; parallel tool calls cut time up to 90%.
- Synchronous subagents are a bottleneck; durable checkpoints + resume; rainbow deploys.
- Eval by **LLM-as-judge rubric**: factual accuracy, citation accuracy, completeness, source
  quality, tool efficiency; plus human review (caught an SEO-farm source-quality bias).

## 2. Open-source systems worth borrowing from

| Project | Core design | Borrow |
| --- | --- | --- |
| **GPT-Researcher** (assafelovic, ~29k★) | Plan-and-Solve + RAG; `deep_research_breadth × depth × concurrency`; parallel sub-queries; citations | breadth/depth/concurrency knobs; resilient "skip failed branch" loop |
| **STORM** (Stanford) | Outline-driven, **multi-perspective** article writing; perspective discovery + simulated expert conversations | generate multiple perspectives before writing |
| **langchain-ai/open_deep_research** | Planner → parallel **researchers** → **critic**; supervisor; human-in-the-loop; MCP tools | explicit critic/reflection stage; HITL gate |
| **HF smolagents open_deep_research** | **CodeAgent** (actions are code), 55% pass@1 GAIA | code-as-action when the environment is a repo |
| **DeerFlow 2.0** (ByteDance, ~81k★) | "Super agent harness": sub-agents, memory, **sandboxes**, skills; streamed `planning_step`/`action_step` events | sandboxed execution; inspectable step events |
| **local-deep-researcher** (LangChain) | Tight loop: search → summarize → **reflect** → refine query | small, cheap, local reflection loop |
| **deep-research-agent** (seen in survey) | Scheduler runtime; researcher/critic; **governed, frozen sources**; auditor; "fails closed, never fakes evidence"; budget sweeps | citation integrity + fail-closed evidence policy |
| **AI Scientist / Agent Laboratory** (Sakana et al.) | Idea → experiment → paper pipelines | staged research artifacts; idea-generation stage |

Repository catalogs: `ai-agents-2030/awesome-deep-research-agent`, `ZhonghaoJiang/Awesome-Issue-Solving`.

## 3. Coding / software-engineering agents (closest to our needs)

- **SWE-agent** introduced the **Agent-Computer Interface (ACI)**: the tool surface matters as much
  as the prompt. Concrete wins (`https://github.com/swe-agent/swe-agent/blob/main/docs/background/aci.md`):
  a **linter gates edits**, a special file viewer shows ~100 lines with scroll/search (not `cat`),
  a search command lists **files with matches only**, and empty output gets an explicit "ran
  successfully, no output" message.
- **OpenHands** (All-Hands-AI): model-agnostic SDK + agent server; task planning/decomposition,
  **automatic context compression**, security analysis, strong ACI; `openhands-aci` adds
  tree-sitter code analysis and linting (`https://docs.openhands.dev/sdk.md`).
- **Agentless** (Xia et al.): a plain **localize → repair → validate** pipeline beat many elaborate
  scaffolds — a reminder to try the simple thing.
- The issue-resolution survey models five phases: **repo preprocessing → localization → repair →
  patch validation → patch selection**, and contrasts pipelines (determinism) with agents (autonomy)
  (`https://arxiv.org/html/2512.22256v2`).
- **Sourcegraph Deep Search** is the reference *code-research* agent: an agentic loop over
  code-search + code-navigation tools, always returning the **list of searches and files read**;
  supports `@repo`/`@file` scoping, and **exhaustive analysis** via sandboxed Lua scripts that
  aggregate over search results into CSV/JSON (`https://sourcegraph.com/docs/deep-search`).

## 4. Discovery tooling an engineering researcher should know

- **Code search**: GitHub code search, **grep.app**, Sourcegraph (self-host/enterprise), **Exa code**
  / `exa-code` — hybrid search over 1B+ pages with a dedicated **code-example index** from GitHub,
  tuned for token-dense code context and measurably fewer hallucinations
  (`https://exa.ai/docs/reference/exa-mcp`).
- **Package/dependency truth**: **deps.dev** (Google) aggregates npm, PyPI, Maven, NuGet, Go,
  Crates, RubyGems + security advisories + resolved dependency graph, CC-BY, cacheable API
  (`https://deps.dev`). Also libraries.io, registry APIs directly.
- **Papers**: arXiv, Semantic Scholar, Papers with Code (benchmarks + leaderboards).
- **Benchmarks to anchor claims**: GAIA, BrowseComp, HLE/GPQA (QA); **DeepResearch Bench**
  (RACE + FACT), FreshWiki (reports); SWE-bench / SWE-bench Pro / Multi-SWE-bench (code).
- **Protocols**: **MCP** for tools, **A2A** for agent-to-agent collaboration
  (see the roadmap survey) — a reason to keep research output structured and portable.

## 5. Cross-cutting design lessons

1. **Search is compression.** Subagents/context isolation exist to compress the corpus into the
   lead's context (Anthropic). Design every research step to *reduce* what has to be held.
2. **Iterative > static retrieval.** Agentic RAG loops (query → read → reflect on sufficiency →
   refine) beat one-shot retrieval for multi-step questions (roadmap survey).
3. **Explicit critic / reflection stage.** planner → researcher → critic shows up repeatedly;
   a reflection pass (local-deep-researcher) catches gaps cheaply.
4. **Cite, then write.** A dedicated citation step (Anthropic's CitationAgent) prevents unsourced
   claims. Fail closed: never fabricate evidence.
5. **Multiple perspectives beat one pass** (STORM), but separate divergence from convergence to
   avoid premature narrowing (see `persona.md`).
6. **Simple pipelines are a real baseline** (Agentless; Anthropic "start simple").
7. **Context engineering is the product**: externalize the plan to memory, compact completed
   phases, retrieve just-in-time, spawn clean-context workers (Anthropic + OpenHands compression).
8. **Evaluate outcomes with a rubric, not a fixed path** — LLM-as-judge on accuracy/citations/
   completeness/source quality/tool efficiency, plus human spot-checks for source bias.
9. **Make the process inspectable**: Sourcegraph returns sources; DeerFlow streams step events;
   the ACI surfaces command output. Observability is how failures get fixed.
10. **Budget explicitly.** Token/cost/latency scale with breadth; publish the effort tier used.

## 6. What this implies for this repo

- Keep the **dynamic-agent core** (frame → plan → gather → verify → synthesize) but expose a
  **simple, inspectable loop** and prefer the cheapest pattern that answers the question.
- Adopt the engineering ACI habits in *our own* tooling: prefer precise search tools, show exact
  commands and outputs, gate on verification.
- Add a first-class **trade study** artifact (weighted criteria + constraints as eliminators) for
  architecture/tooling/datasource decisions (`templates/trade-study.md`).
- Treat **source quality** and **citation integrity** as hard rules (already in `design.md` §4).
- Keep an **effort tier** in every report (quick scan / standard / deep dive) so cost is explicit.
