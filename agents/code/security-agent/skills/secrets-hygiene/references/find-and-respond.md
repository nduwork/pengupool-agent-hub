# Finding secrets and responding to a leak

## Patterns

Regular expressions for `grep -E` / `git grep -E`. They over-match on purpose; classify each
hit by hand. Every command below prints locations only.

| Kind | Pattern |
| --- | --- |
| Private key block | `BEGIN [A-Z ]*PRIVATE KEY` |
| AWS access key id | `(AKIA|ASIA)[0-9A-Z]{16}` |
| GitHub token | `gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}` |
| Slack token | `xox[abpors]-[A-Za-z0-9-]{10,}` |
| Google API key | `AIza[0-9A-Za-z_-]{35}` |
| Stripe live key | `(sk|rk)_live_[A-Za-z0-9]{20,}` |
| JWT | `eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.` |
| URL with credentials | `[a-z][a-z0-9+.-]*://[^/:@[:space:]]+:[^@[:space:]]+@` |
| Assigned secret | `(password|passwd|secret|token|api[_-]?key|private[_-]?key)["']?[[:space:]]*[:=][[:space:]]*["'][^"']{8,}` |

## Commands

Working tree, locations only:

```bash
git grep -nIE 'BEGIN [A-Z ]*PRIVATE KEY' | cut -d: -f1,2
```

Untracked and ignored files too (still locations only):

```bash
grep -rnIE --exclude-dir=.git --exclude-dir=node_modules '<pattern>' . | cut -d: -f1,2
```

History, commit ids only:

```bash
git log --all -G '<pattern>' --format='%h %ad %an %s' --date=short
```

For one commit, which files matched:

```bash
git show --name-only --format= <sha> | while IFS= read -r f; do
  git show "<sha>:$f" 2>/dev/null | grep -qE '<pattern>' && printf '%s\n' "$f"
done
```

Staged diff before a commit:

```bash
git diff --cached -U0 | grep -cE '<pattern>'   # count only; non-zero means stop and look by file
```

Never pipe a match to the terminal, a message or a file without the `cut`, `-l`, `-c` or
`-q` that drops the matched text.

## Is it real?

Placeholder or real: values like `changeme`, `xxx`, `<your-key>`, `test`, all-zero, or in a
file named `*.example`/`*.sample` are placeholders. A hit in a test fixture may still be real;
ask. Whether a credential is live is for the owner to confirm with the provider; you never call
the provider with it.

## Leak runbook (owner acts; you prepare)

1. **Contain**: owner revokes or rotates the credential at the provider. If it cannot be revoked
   quickly, restrict it (IP allowlist, scope down) as a stopgap.
2. **Replace**: code reads it from the environment or the secret store; startup fails clearly
   when it is missing; `.env.example` documents the name.
3. **Review use**: owner checks provider audit/access logs from the first exposing commit's date
   to the rotation time.
4. **Purge (optional, owner decision)**: rewriting history needs every collaborator to re-clone
   and does not remove forks, caches or CI logs. If chosen, use `git filter-repo` with a
   replacement file, then the owner force-pushes and asks the host to drop cached views. You
   write the plan; you do not run the force-push.
5. **CI logs**: if a job printed it, the owner deletes those run logs.
6. **Prevent**: gitignore rules, a pre-commit secret check and a CI scan, agreed with the owner
   (a new tool is a dependency change under the org's supply-chain policy).
7. **Record**: one line in the report: what kind, where, when exposed, when rotated. No value.

## Review checklist for a project

- [ ] No secret values in the tree or history (or each found one is rotated and listed).
- [ ] Real `.env*`, key and credential files are gitignored; `.env.example` exists.
- [ ] Config reads secrets in one place and fails fast when one is missing.
- [ ] Logs redact secret-named keys centrally.
- [ ] CI uses platform secrets or OIDC, scoped per environment; untrusted PRs get none.
- [ ] No `set -x` or `echo` of secrets in CI steps; third-party actions pinned to a SHA.
- [ ] Images carry no secrets in layers.
- [ ] Each secret has an owner and a rotation path.
