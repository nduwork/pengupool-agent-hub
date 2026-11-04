---
name: secrets-hygiene
description: Find leaked secrets and keep credentials out of code, logs and CI. Use when a key, token or password may have been committed, printed or shared, when wiring secrets into an app or pipeline, or when reviewing how a project stores and rotates credentials. Reports each secret by location and type only, never its value, and walks the owner through rotation and cleanup.
triggers:
  - leaked secret
  - committed a key
  - secret scan
  - api key in code
  - rotate credentials
  - .env
  - secrets in CI
  - secret manager
---

# Secrets hygiene

A secret is anything that grants access: API keys, tokens, passwords, private keys, signing
keys, connection strings with credentials, webhook signing secrets, session secrets.

**The one rule:** you report where a secret is and what kind it is. You never print, copy, log,
message, commit or upload its value. When output might contain one, cut it to `file:line`
before you read or share it.

## 1. Find

Search the working tree and history, printing locations only. Patterns and commands are in
[references/find-and-respond.md](references/find-and-respond.md).

1. **Working tree**: `git grep -nIE '<pattern>' | cut -d: -f1,2` per pattern.
2. **History**: `git log --all -G '<pattern>' --format='%h %ad %s' --date=short` lists commits
   that added or removed a match without showing the content.
3. **Usual places**: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `credentials*`,
   `config/*.yml`, notebooks with output cells, CI files, Dockerfiles (`ENV`/`ARG`), test
   fixtures, shell history files committed by accident.
4. **Optional scanner**: if `gitleaks` or `trufflehog` is already installed, run it with
   redaction on (`gitleaks ... --redact`). Installing one is a dependency change: ask the owner
   first. Without a scanner the grep pass above is the fallback.
5. **Classify each hit**: real or placeholder/test value; live or already revoked (you can tell
   only from context or the owner, never by trying the credential); public or private repo;
   pushed or local only.

Never test whether a found credential works.

## 2. Respond to a leak

Severity: a live secret in a pushed public repo is Critical; pushed private repo is High;
committed but not pushed is Medium (fix before push); in an ignored local file is Low.

Order matters:

1. **Rotate first.** A secret that reached a remote is compromised from that moment; removing it
   from history does not undo copies, forks or caches. The owner (or the secret's owner)
   revokes and reissues it. You prepare the steps; you do not revoke.
2. **Replace in code** with a read from the environment or the secret store, and fail fast at
   startup when it is missing.
3. **Check for use**: ask the owner to review the provider's access logs for the exposure
   window.
4. **Purge history only when the owner decides to** (it rewrites shared history and needs a
   force-push and every clone re-synced). Propose the command; never run a force-push yourself.
5. **Prevent recurrence**: `.gitignore` entry, a committed `.env.example` with placeholders, and
   a pre-commit or CI scan if the owner agrees.

Leak runbook details: [references/find-and-respond.md](references/find-and-respond.md).

## 3. Keep secrets out

**In code**
- Read from the environment or a secret store at runtime; one config module owns the reads.
- Commit `.env.example` with names and placeholder values; gitignore real `.env*`, keys and
  credential files.
- Separate secrets per environment; a dev key never works in production.
- Before committing, count matches in the staged diff without printing them:
  `git diff --cached -U0 | grep -cE '<pattern>'`; non-zero means find the file and fix it.

**In logs and errors**
- Never log request headers, full bodies, connection strings or config objects wholesale.
- Redact by key name (`authorization`, `cookie`, `password`, `token`, `secret`, `key`) in the
  logger, not at each call site.
- Error messages and stack traces shown to callers carry no config values.

**In CI**
- Use the platform's secret store (repository/environment secrets, protected and masked
  variables) or OIDC federation to the cloud instead of long-lived keys.
- Scope secrets to the environment and branch that need them; forks and untrusted pull-request
  workflows get none.
- Never `echo` a secret, never enable shell tracing (`set -x`) in a step that has one, and mask
  any value fetched at runtime before using it.
- Pass secrets via environment variables or files, not command-line arguments (visible in
  process lists and logs).
- Pin third-party CI actions to a full commit SHA; an action sees the job's secrets.

**In containers and infrastructure**
- No secrets in image layers (`ENV`, `ARG`, copied files); use build secrets or runtime
  injection.
- Infrastructure code references the secret store; state files that contain secrets are
  encrypted and access-controlled.

## 4. Stores and rotation

Pick what the platform already uses: a cloud secret manager, Vault, Kubernetes secrets backed by
an external store, or CI-native secrets. Look for: least-privilege access per service, audit
logging on reads, versioning, and a rotation path that lets old and new values overlap. Prefer
short-lived, automatically issued credentials (OIDC, dynamic database users) over static ones.

Rotation steps: create the new value, deploy it alongside the old, switch consumers, verify,
then revoke the old one.

## Report

```text
| # | Sev | Where | Type | Status | Next step (owner) |
| 1 | High | deploy/ci.yml:42 (commit a1b2c3d) | cloud access key | pushed, private repo | rotate, then replace with OIDC |
```

No values, no partial values, no hashes of values.
