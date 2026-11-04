---
name: defensive-shell
description: Write and review bash and sh scripts that fail safely on bad input, missing files and errors. Use when writing, reviewing or fixing a shell script, CI step, installer, deploy or cleanup script, or setting up shellcheck. Covers strict mode, quoting, argument and input handling, temp files and cleanup traps, safe deletes, and shellcheck with documented exceptions.
triggers:
  - shell script
  - bash script
  - shellcheck
  - set -euo pipefail
  - review this script
  - CI step script
  - cleanup script
---

# Defensive shell

Shell scripts run with the user's full rights and treat every unquoted value as code. Most
shell bugs that matter are one of: an unquoted variable, an ignored failure, an empty variable
in a destructive command, or untrusted text reaching `eval` or a command line.

## 1. Header and failure handling

- Shebang names the shell the script needs: `#!/usr/bin/env bash` for bash features, `#!/bin/sh`
  only if it is really POSIX.
- Strict mode near the top: `set -Eeuo pipefail` (bash). Know its gaps: `-e` is ignored inside
  `if`/`&&`/`||` conditions and in command substitution in some contexts; check critical steps
  explicitly.
- Required variables fail with a message: `: "${TARGET_DIR:?TARGET_DIR is required}"`.
- Optional ones get explicit defaults: `"${LOG_LEVEL:-info}"`.
- Errors go to stderr with a non-zero exit; an `ERR` trap that prints the line number helps
  debugging.

## 2. Quoting and expansion

- Quote every expansion: `"$var"`, `"$(cmd)"`, `"${arr[@]}"`. Unquoted values split on spaces
  and expand globs.
- Hold lists in arrays, never in space-separated strings.
- End options before user-supplied operands: `rm -- "$f"`, `grep -- "$pattern" "$file"`.
- Use `[[ ... ]]` in bash; in POSIX `sh`, quote both sides of `[ ... ]`.
- `printf '%s\n' "$x"` instead of `echo "$x"` for data (echo mangles `-n`, backslashes).

## 3. Untrusted input

Arguments, environment, file contents, filenames and output of other programs are untrusted.

- Validate before use with a `case` pattern or `[[ $x =~ ^[A-Za-z0-9._-]+$ ]]`; reject, do not
  "clean".
- Never `eval` input, and never build a command string to run later; build an array and run
  `"${cmd[@]}"`.
- No `source` of files a less trusted user can write.
- Read lines with `while IFS= read -r line; do ...; done < file`; iterate files with
  `find ... -print0 | while IFS= read -r -d '' f` or a glob, never by parsing `ls`.
- Do not pass secrets on the command line (visible in process lists); use env or a file with
  `0600`. Never `set -x` in a script that handles a secret.

## 4. Temp files and cleanup

```bash
tmp=$(mktemp -d) || exit 1
trap 'rm -rf -- "$tmp"' EXIT
```

- Always `mktemp`, never a fixed `/tmp/name` (races and symlink attacks).
- One `EXIT` trap that cleans up everything; `INT`/`TERM` traps exit so `EXIT` runs.
- Write to a temp file in the target's directory, then `mv` into place for atomic updates.
- Set `umask 077` before creating files that may hold sensitive data.

## 5. Destructive commands

- Guard every `rm -rf`, `mv`, `chmod -R` on a variable path: non-empty, resolved, under an
  expected root, not the root itself.

```bash
root=$(cd -- "$ROOT" && pwd -P) || exit 1
real=$(cd -- "${dir:?}" && pwd -P) || exit 1        # resolves symlinks and ..
[[ $real == "$root"/?* ]] || { printf 'refusing %s\n' "$real" >&2; exit 1; }
rm -rf -- "$real"
```

- Offer `--dry-run` for scripts that delete, move or deploy; print what would happen.
- Make reruns safe: `mkdir -p`, check before create, skip what is already done.

## 6. Portability and tools

- `command -v tool >/dev/null || { echo "needs tool" >&2; exit 1; }` instead of `which`.
- macOS ships bash 3.2 and BSD tools: `sed -i`, `readlink -f`, `date -d`, `mapfile` differ.
  Either require bash 4+/GNU tools explicitly or use the portable form.
- Use `$(...)` not backticks; `$((...))` for arithmetic.

## 7. ShellCheck

Run `shellcheck` on every script when it is installed (`shellcheck -x script.sh`; `-x` follows
`source`). If it is not, do the manual pass in sections 1-5. Installing it, or adding it to CI,
is a dependency change: ask the owner first.

- Fix findings rather than silence them. A suppression sits on the line it covers with a reason:
  `# shellcheck disable=SC2086  # word-splitting of FLAGS is intended`.
- A project-wide `.shellcheckrc` sets the dialect (`shell=bash`) and only the exclusions the
  team agreed on, each with a comment.
- In CI, fail the job on warnings or above for changed scripts.

The codes worth knowing and their fixes: [references/shellcheck.md](references/shellcheck.md).

## Review report

Same format as the other skills: severity, `file:line`, what goes wrong (and with what input),
the fix, and the check: usually a run with a filename containing spaces, `*` or a leading `-`,
an unset variable, or a failing middle command in a pipe.
