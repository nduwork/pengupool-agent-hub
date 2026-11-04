# PenguPool agent hub

The catalog of helper agents for PenguPool. Use it through PenguPool only.

Each plugin is a helper agent: a folder `agents/<group>/<name>/` in this repository
with its own persona (`AGENTS.md`) and skills (`skills/<name>/SKILL.md`),
following this repository's `main`. A helper is active only while it is
added to a team or group, and its skills belong to that helper alone.

Use the catalog through PenguPool; do not install these helpers into an agent.
The catalog is `.pengupool/catalog.json`, a PenguPool-only file. The
`.claude-plugin/marketplace.json` beside it is kept, with the same helpers and
entries, for PenguPool installs that still read it; it is removed once a PenguPool
release reads only `.pengupool/catalog.json`. `check_catalog.py` fails when the two
disagree.

This repository holds the catalog and every helper. A helper's memories and task logs are
not in Git: PenguPool keeps them per skill in its own database
(`~/.pengupool/v2/agents.db`), so adding or updating a helper never touches
them.

Keep every `AGENTS.md` and `SKILL.md`
harness- and model-agnostic and generalizable: `check_catalog.py` enforces it.

## Use it in PenguPool

1. Skill library → **Marketplace** → add this repository's URL. PenguPool
   clones it with your Git credentials (it is private) and lists the helpers.
2. **Add** a helper. PenguPool clones this repository at the latest commit of
   the helper's `ref` (`main`) and registers its `agents/<group>/<name>` folder in the Skill library. A
   helper already registered from a local checkout shows as added.
3. Put the helper to work by adding it to a team or group, from the map's
   Skill agent pool or from Teams. It runs there as its own agent session.

## Helpers by group

Each helper does one kind of work and leaves the rest to the others in its
group. The group is the entry's `group`, which PenguPool's Helper agents page
groups by; give every new helper one of these five. The catalog is the source
of truth: a helper's folder sits at `agents/<group>/<name>/`, and
`check_catalog.py` fails when the two disagree. To move a helper to another
group, change its `group` and move its folder in the same PR.

| Group | Helper | Does |
| --- | --- | --- |
| Team (`team`) | `team-lead-agent` | Leads a team from the root of its tree: passes work along the tree, routes by role, queues the owner's ideas and proposes them as epics |
| Code (`code`) | `dev-workflow-agent` | Plans a change in thin slices, builds test-first, debugs by root cause, simplifies, verifies |
| | `api-design-agent` | Drafts and reviews API contracts and boundaries, records decisions as ADRs |
| | `security-agent` | Hardens inputs, auth, secrets and shell scripts; ranks findings by severity |
| | `pr-review-agent` | Peer-reviews a PR read-only (optional adversarial review, subagents, delta re-review); optional author-side flowchart |
| Operations (`operations`) | `git-ci-agent` | Triages a failed GitHub Actions run and proposes a fix |
| | `git-runner-agent` | Sets up and keeps healthy the self-hosted runners |
| | `gcp-service-agent` | Sets up, deploys and runs a service on Google Cloud (Cloud Run first) |
| | `ops-readiness-agent` | Instruments, measures, runs launch checklists and incident response |
| | `worktree-cleanup-agent` | Removes merged, idle worktrees and branches; lists unmerged ones for the owner |
| Apps (`apps`) | `frontend-ui-agent` | Designs and builds PenguPool's desktop UI; draws README and docs diagrams (D2, Mermaid) |
| | `ios-app-agent` | Signs and ships an iOS app to TestFlight and the App Store |
| | `macos-app-agent` | Signs, notarizes and packages a macOS app for distribution outside the Mac App Store |
| | `motion-video-agent` | Makes motion videos as deterministic code: brief, stills review, frame-exact render, sound, QA |
| | `logo-design-agent` | Designs logos and brand marks from brief to tested SVG and delivery kit |
| Research and data (`research`) | `research-agent` | Answers engineering research questions with sourced findings |
| | `data-analysis-agent` | Explores data, writes SQL, validates quality, runs statistics; aggregates only |
| | `bioinfo-agent` | Nextflow pipelines, single-cell QC and scvi-tools modelling, question scoping |

Teams that work well together (add the helpers next to the repository
members that own the code):

- **Idea to plan:** `team-lead-agent`, with `research-agent` when an idea
  needs facts first.
- **Feature:** `dev-workflow-agent` + `pr-review-agent`, with
  `api-design-agent` for a new interface and `security-agent` for anything that
  handles untrusted input or secrets.
- **Release:** `ops-readiness-agent` + `git-ci-agent`, with `git-runner-agent`
  when the self-hosted runners are involved.
- **Analysis:** `data-analysis-agent` + `research-agent`, with `bioinfo-agent`
  for sequencing or single-cell work.

## Entry format (`.pengupool/catalog.json`)

`{"name"?, "description"?, "agents": [...]}`. Each entry in `agents`:

| Field | Meaning |
| --- | --- |
| `name` | The helper's name, unique here (case-insensitive) |
| `description` | What the helper does, one or two sentences |
| `group` | Its group: `team`, `code`, `operations`, `apps` or `research` |
| `capabilities` | Its skills; PenguPool reads them as capabilities |
| `harness`, `requires` | Not used: every helper runs in any agent harness |
| `repo` | `https://github.com/nduwork/pengupool-agent-hub.git` |
| `path` | `agents/<group>/<name>`: the folder sits under its group |
| `ref` | The branch PenguPool follows: `main` |
| `sha` | Not used here: a helper of this repository follows its `ref`. Only a helper kept in its own repository may pin a full 40-character commit |
| `credits` | Optional. The public third-party repositories the helper was distilled from, a list of `{"name", "url"}` with an https `url`, by convention `[{"name": "<owner>/<repo>", "url": "https://github.com/<owner>/<repo>"}]`. Shown to people only, never loaded into an agent's context. Leave it out when there is none; the owner's own repositories are not credited |

`capabilities` are the skill names under `skills/<name>/SKILL.md`; PenguPool uses
them for routing and the map's pool. A helper kept in its own repository has a
`repo` and no `path`.

The old `.claude-plugin/marketplace.json` maps field for field: `plugins` →
`agents`, `category` → `group`, `keywords` → `capabilities`, `source.url` →
`repo`, `source.path` → `path`, `source.ref` → `ref`, `source.sha` → `sha`,
`credits` → `credits` (plugin validators warn that the field is unknown and ignore it).

## How helper changes reach installs

There are no pins: every helper follows `main`. A merged change to a helper's
folder reaches the installed helpers on their next library sync, with no second
PR. Review is the gate: nothing reaches `main` without a reviewed pull request.

## What a helper folder must have

The **Check catalog** run on every PR (`scripts/check_catalog.py`) checks this. It is
the only check: PenguPool does not check a helper again when it adds one.

1. `AGENTS.md` at the folder root: the helper's persona and how to use its
   skills.
2. At least one `skills/<name>/SKILL.md`, each with:
    - `name` and `description` in its front matter, and `name` equal to the
      folder name;
    - only these front-matter keys: `name`, `description`, `license`,
      `compatibility`, `metadata`, `allowed-tools`, `triggers`;
    - a body of at most 8 KiB and at most 500 lines.
3. No secrets in `AGENTS.md` or anywhere under `skills/`. `check_catalog.py` rejects
   anything that looks like a key or token, so use placeholders such as `<token>`.
4. Descriptions say what the helper or skill does, its functions and features,
   not where its ideas came from. This holds for the catalog `description`,
   each `SKILL.md` `description` and `AGENTS.md`. Credit goes in two places
   only: the catalog entry's `credits` field names the public repositories a
   helper was distilled from (display only, in both catalog files), and when a
   license requires credit for copied material, a short `## Credits` section
   at the very end of that `SKILL.md`.
5. It works in any agent harness. `AGENTS.md` and `skills/` are the whole
   layout: no `.claude/`, `.codex/`, `.pi/` or other harness folder, and no
   skill links. `AGENTS.md` and each `SKILL.md` say "run the command", "read
   the file", "message your parent with `pengupool send`" and "ask a
   sub-agent if your agent can", and never name a harness-only tool, slash
   command, config file (`CLAUDE.md`, `~/.claude`) or model id. Its
   `AGENTS.md`, `README.md`, manifests, scripts and skills name no harness
   (claude, codex, gemini, copilot, opencode, pi, omp) either.
6. A feature only one harness has (a particular tool, making video or images)
   is a clearly optional add-on named for its harness: a folder
   `addons/<harness>/` or a skill whose name contains the harness, and the
   core works without it. A line that points at the add-on may name its
   harness. `logs/`, `CHANGELOG.md`, `docs/` and `tests/` are history and
   notes, not instructions, and are not checked. `check_catalog.py` rejects
   anything else, and lists the few tools a helper operates that are built on
   a harness (git-ci-agent's local model runner) in `ENGINE_FILES`.

Nothing else is required. PenguPool's session context names the helper's
folder and lists its skills, and the agent reads them from there.

## Propose a helper or a change

Changes reach `main` through pull requests: propose, then a maintainer reviews
and merges. Open a PR that changes `agents/<group>/<name>/` (for a new helper, add
the folder and its entry in both catalog files, with no `sha`). Once it is
squash-merged, it reaches installed helpers on their next sync.

Every PR runs the **Check catalog** workflow, which runs `scripts/check_catalog.py`. It checks
that the catalog has the format above, that `.claude-plugin/marketplace.json` agrees with it, that
names are unique, each helper here sits at `agents/<group>/<name>` and has
no `sha` (a helper kept elsewhere may pin one, which must exist on its repository), each helper has
an `AGENTS.md`, each `skills/<name>/SKILL.md` has a `description` and a
`name` matching its folder, and every `pengupool <command>` a helper's
instructions name is one `pengupool help` lists (`PENGUPOOL_COMMANDS`). This repository's helpers are
read from the checkout (on a PR, the merge commit); others through the GitHub API, so a helper kept
elsewhere must be in a public repository. The workflow runs on a GitHub-hosted runner and uses no
secret. Run the script locally with `python3 scripts/check_catalog.py`.
