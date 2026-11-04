# Debugging a failed Nextflow run

## Find the failing task

1. The console error block names the process, the exit status, the command and the work
   directory. If the console is gone: `.nextflow.log` (search for `ERROR` and `Caused by`), or
   `nextflow log` to list runs and `nextflow log <run_name> -f name,status,exit,workdir -F "status == 'FAILED'"`.
2. In the work directory (`work/ab/cdef…`):

| File | What it tells you |
| --- | --- |
| `.command.sh` | The script exactly as run, with variables filled in |
| `.command.run` | The wrapper: staging, container call, resource setup |
| `.command.err` / `.command.out` | The tool's stderr / stdout |
| `.command.log` | Both streams plus scheduler output |
| `.exitcode` | The exit status (missing = killed before the script ended) |
| `.command.trace` | CPU, memory, I/O of the task when tracing is on |

3. Reproduce in place: `cd` there and `bash .command.run` (uses the same container and staging).
   Edit `.command.sh` to try a fix; then move the fix into the module or config.

## By symptom

| Symptom | Usual cause | Fix |
| --- | --- | --- |
| Exit 137 | Killed (SIGKILL), mostly out of memory | Raise memory for that label or process; retry with `task.attempt` scaling |
| Exit 143 | Terminated (SIGTERM), mostly scheduler time or memory limit | Raise `time`/`memory`; check the scheduler's own log |
| Exit 104, 134, 139, 247 | Crash, often memory pressure | Same as 137, then read `.command.err` |
| Exit 127 | Command not found | Tool missing from the container or conda env; check the image and tag |
| Exit 126 | Not executable | Script in `bin/` lacks `chmod +x` |
| Exit 1 | The tool itself failed | Read `.command.err`; usually bad input, wrong reference, or an argument |
| "Missing output file(s)" | Output glob does not match, or the tool wrote elsewhere | `ls` the work dir; fix the glob or the tool's output flag |
| "No such file" for inputs | Relative or wrong paths in the samplesheet; path not mounted in the container | Absolute paths; add the path to the container's bind or mount config |
| "Process requirement exceeds available CPUs/memory" | Local executor and a request larger than the machine | Lower the cap (`resourceLimits` or `--max_*`) |
| Container pull fails | Network, registry auth, or cache dir not writable | Set `NXF_SINGULARITY_CACHEDIR`/`NXF_APPTAINER_CACHEDIR`; pre-pull; try another engine |
| Hangs with no tasks running | A process waits on a channel that never closes (`groupTuple` without size, a queue channel used where a value was meant) | See channels.md |
| Wrong number of tasks | Inputs paired by order, or a reference given as a queue channel | `join` by key; make references value channels |

## When `-resume` re-runs everything

The cache key covers the script, the inputs (path, size, modification time), the container and
the relevant config. Things that break it:

- Running from a different launch directory or with a different `-work-dir`.
- Deleting `work/` or `.nextflow/`; `nextflow clean` without `-k`.
- A shared file system that changes modification times: set `cache 'lenient'` (path and size only).
- Inputs regenerated each run (a step that rewrites a file even when unchanged).
- A changed `ext.args`, container tag or `params` value used in the script: correct behaviour.

Compare two runs with `-dump-hashes` to see which part of the key changed.

## Ask for more visibility

`-with-report report.html -with-trace -with-timeline` shows each task's peak memory and time;
size resource labels from those numbers, not guesses. `NXF_DEBUG=1` or `-process.debug` adds
detail to the log for staging and container problems.

## Do not

- Delete `work/` or results to "start clean" without asking; it throws away the cache and the
  evidence.
- Raise every resource limit at once; fix the process that failed.
- Paste `.command.sh` into a message when it contains sample names or patient paths; summarise.
