---
name: nextflow-pipelines
description: Writes, reviews, runs and debugs Nextflow DSL2 pipelines — processes, modules and subworkflows, channels and operators, configs and profiles, containers, nf-core conventions and nf-core pipeline runs. Use when building or changing a pipeline, choosing a channel operator, setting resources or profiles, running an nf-core pipeline on local or public data, or working out why a run failed or will not resume.
triggers:
  - nextflow
  - nf-core
  - dsl2
  - pipeline failed
  - work directory
  - -resume
  - samplesheet
  - channel operator
  - nf-test
---

# Nextflow pipelines

Three jobs: **write** a pipeline or module, **run** an existing one (often nf-core), **debug** a run
that failed. Find out which before touching anything. Never paste samplesheet rows or sample names
into a reply; say "12 samples, 24 FASTQ pairs" and give the path.

## Before anything

1. `nextflow -version` (DSL2 needs 22.04+; current nf-core templates expect 24.04+ for
   `resourceLimits`), the container engine (`docker info`, `singularity --version`), Java 17+ for current releases.
2. Where it will run: laptop, HPC scheduler, or cloud batch. That decides the profile and the
   executor; ask if unclear.
3. For an existing pipeline, read `main.nf`, `nextflow.config`, `conf/` and the docs page for the
   pinned revision before changing parameters.

## Writing DSL2

- One tool per process. Inputs as `tuple val(meta), path(files)` where `meta` is a map with at
  least `id`; carry it through so outputs stay labelled without parsing file names.
- Every process has `tag "$meta.id"`, a `label` for its resource class (`process_low`, `_medium`,
  `_high`), a pinned `container`, `when: task.ext.when == null || task.ext.when`, tool arguments
  from `task.ext.args`, and an output `versions.yml` (or a `topic` channel) for reporting.
- Add a `stub:` block that `touch`es the declared outputs so `-stub-run` tests wiring in seconds.
- Group processes into subworkflows with `take:`, `main:`, `emit:`. Keep `main.nf` thin.
- Publish through config (`withName: 'FOO' { publishDir = [...] }`) or workflow outputs, not
  hard-coded paths inside modules.
- Validate inputs at the edge: `channel.fromPath(..., checkIfExists: true)`, a samplesheet schema
  (nf-schema) with absolute paths, and a clear error for a missing column.
- Prefer an existing nf-core module (`nf-core modules install <tool>`) over writing a new one; if
  you patch one, record it with `nf-core modules patch`.

Channel and operator choice, with the traps that cause silent wrong results:
[references/channels.md](references/channels.md).

## Configuring

- Resources by label in `conf/base.config`; retry on kill signals with
  `errorStrategy { task.exitStatus in 137..143 ? 'retry' : 'finish' }`, `maxRetries 2`, and
  `memory { 6.GB * task.attempt }`. Cap with `process.resourceLimits` (newer) or the
  `--max_cpus/--max_memory/--max_time` params (older nf-core).
- One profile per environment (`docker`, `singularity`, `conda`, a site profile for the
  scheduler) plus `test` with tiny data. Profiles combine: `-profile test,docker`.
- Single dash = Nextflow option (`-resume`, `-profile`, `-r`); double dash = pipeline parameter.
  Put many parameters in `-params-file params.yaml` rather than a long command.
- Pin: `-r <tag>` for remote pipelines, container tags (ideally digests), and the Nextflow
  version via `manifest.nextflowVersion`.

## Running

1. Run the test profile first: `nextflow run <pipeline> -r <tag> -profile test,<engine> --outdir test_out`.
   It must finish before real data.
2. Build or validate the samplesheet; check every path exists and read pairs match. Report counts.
3. Confirm the reference (genome build, annotation version) and the analysis options with the
   owner before the full run. Add `-resume` from the start; it costs nothing.
4. Add `-with-report -with-trace -with-timeline` so resource use is visible afterwards.
5. Check the end: "Succeeded" in `.nextflow.log`, the MultiQC report, the expected outputs.

nf-core run notes (rnaseq, sarek, atacseq, public data from GEO/SRA):
[references/nf-core-runs.md](references/nf-core-runs.md).

## Debugging a failed run

Read the error block in the console or `.nextflow.log`, find the failing task's work directory,
and read `.command.err`, `.command.log`, `.command.sh`, `.exitcode` there. Reproduce inside that
directory with `bash .command.run` before changing the pipeline. Full triage table (exit codes,
missing outputs, resume misses, container and staging problems):
[references/debugging.md](references/debugging.md).

## Testing and review

- `-stub-run` for wiring, `-profile test` for a real small run, `nf-test` for module and
  pipeline tests with snapshots when the repo uses it.
- `nextflow lint` (25.04+) or `nf-core pipelines lint` when available.
- In review, look for: unpinned containers, queue channels paired by position, `groupTuple`
  without a size, outputs published from inside modules, absolute paths in code, missing stubs.

## Report

Pipeline and revision, Nextflow version, profile, command line, run status, failing process and
exit code if any, what you changed and why, paths to the report and outputs. Aggregated counts
only.
