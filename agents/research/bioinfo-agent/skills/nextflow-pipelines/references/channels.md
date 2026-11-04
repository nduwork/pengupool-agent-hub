# Channels and operators

## Two kinds of channel

- **Queue channel**: a stream; each item is consumed once. `channel.fromPath`, `fromFilePairs`,
  process outputs.
- **Value channel**: one item, read any number of times. `channel.value(x)`, the result of
  `.first()` or `.collect()`, a plain file passed as a process input.

A reference genome, an index or a config file should be a value channel. If it is a queue
channel, a process with a second input runs exactly once and then stops, with no error.

## Pairing inputs

A process with several queue-channel inputs pairs them **by arrival order**, and stops at the
shorter one. Order is not stable across runs. Never rely on it for per-sample data.

| Need | Use |
| --- | --- |
| Match items from two channels by sample | `a.join(b)` on the first tuple element (the `meta` map or `meta.id`); add `failOnMismatch: true` so a missing partner fails loudly |
| Every item × every item (samples × references) | `a.combine(b)`; `combine(b, by: 0)` for a keyed cross |
| Gather per-sample pieces (lanes, chunks) | `groupTuple()` with `size:` or a `groupKey(id, n)` so it emits as soon as a group is complete instead of at the end of the run |
| Everything into one task (MultiQC, merge) | `.collect()` (flattens) or `.toList()` (keeps items whole) |
| Split one stream by a condition | `branch`, one labelled condition per line (e.g. `tumour:` on `meta.status == 1`, then a catch-all `normal: true`) |
| Send one item to two shapes | `multiMap` |
| Merge streams of the same shape | `mix` |
| Reshape | `map`; keep `meta` first in every tuple |

## Samplesheets

`channel.fromPath(params.input).splitCsv(header: true)` then `map` each row to
`[ meta, [ file(r.fastq_1, checkIfExists: true), ... ] ]`. Better: validate with an nf-schema
JSON schema (`samplesheetToList`) so types, required columns and paths are checked up front.
Single-end vs paired-end goes in `meta.single_end`, not in file-name guesses.

## Common mistakes

- Using a channel twice in DSL2 is fine (it is forked automatically); consuming it with
  `.view()` is fine too. Using `.subscribe` to "read" a value inside the workflow is not.
- Modifying `meta` in place inside a closure changes it for every channel holding that map.
  Copy it: `meta + [ key: value ]`.
- `groupTuple` on a key that holds a file path or a whole map with differing fields never
  groups. Group on a stable id.
- `.collect()` on an empty channel emits nothing, so downstream processes silently skip. Use
  `.ifEmpty { error "no inputs matched ${params.input}" }` where an empty input is a mistake.
- File name collisions when staging many files with the same name: use
  `path(files, stageAs: 'in/?/*')`.
- Globs in `output:` that do not match what the tool writes produce "Missing output file(s)".
  Check the tool's real output names in the work directory.
