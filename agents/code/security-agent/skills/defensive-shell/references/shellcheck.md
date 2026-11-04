# ShellCheck codes worth knowing

Codes are grouped by what goes wrong. Fix the cause; suppress only with a reason on the line.

## Splitting, globbing and quoting

| Code | Meaning | Fix |
| --- | --- | --- |
| SC2086 | unquoted variable splits and globs | quote it; use an array for lists |
| SC2046 | unquoted `$(...)` splits | quote it, or read into an array with `mapfile`/`while read` |
| SC2068 | unquoted `$@` / `${arr[@]}` | `"$@"`, `"${arr[@]}"` |
| SC2206 / SC2207 | splitting into an array | `read -ra arr <<< "$s"` or `mapfile -t arr < <(cmd)` |
| SC2016 | `$` inside single quotes will not expand | intended? fine; else use double quotes |
| SC2115 | `rm -rf "$dir/"` with `$dir` possibly empty | `"${dir:?}/"` |

## Commands and control flow

| Code | Meaning | Fix |
| --- | --- | --- |
| SC2155 | `local x=$(cmd)` hides cmd's exit status | declare, then assign on its own line |
| SC2181 | `if [ $? -ne 0 ]` | `if ! cmd; then` |
| SC2015 | `a && b || c` is not if/else | write `if a; then b; else c; fi` |
| SC2164 | `cd` without failure check | `cd "$d" || exit` |
| SC2251 | bare `! cmd` skips `set -e`, so a test "expecting failure" never fails | `cmd && exit 1` |
| SC2012 / SC2045 | parsing `ls` | glob or `find -print0` |
| SC2009 | `ps | grep` | `pgrep` |
| SC2162 | `read` without `-r` mangles backslashes | `read -r` |
| SC2034 | variable assigned but unused | remove, or `export` it if meant for a child |
| SC2154 | variable used but never assigned | set it, or `: "${VAR:?}"` if it comes from env |

## Portability (POSIX `sh`)

| Code | Meaning | Fix |
| --- | --- | --- |
| SC3010 | `[[ ]]` in sh | `[ ]` with quotes, or switch shebang to bash |
| SC3043 | `local` in sh | avoid, or switch to bash |
| SC3037 | `echo` flags in sh | `printf` |

## Parser and source

| Code | Meaning | Fix |
| --- | --- | --- |
| SC1091 | sourced file not followed | run with `-x`, or `# shellcheck source=path` |
| SC2148 | no shebang | add one |

## Configuration

`.shellcheckrc` at the repository root:

```text
shell=bash
external-sources=true
# disable=SCxxxx   # one line per agreed exclusion, each with its reason
```

Optional checks worth turning on for strict projects: `enable=require-variable-braces`,
`enable=check-unassigned-uppercase`. Turn on everything (`--enable=all`) only with the team's
agreement; then document each exclusion.

## CI

Run on changed `*.sh` files and files with a shell shebang:

```bash
git diff --name-only --diff-filter=ACM origin/main... \
  | while IFS= read -r f; do
      case "$f" in *.sh) printf '%s\0' "$f" ;; esac
    done \
  | xargs -0 -r shellcheck -x --severity=warning
```

Use the project's existing CI and pre-commit setup; adding a new action or hook is a dependency
change to agree with the owner.
