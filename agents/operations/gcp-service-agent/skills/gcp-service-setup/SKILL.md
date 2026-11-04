---
name: gcp-service-setup
description: |
  Use when setting up, deploying, hardening or cutting the cost of a service on Google Cloud, Cloud Run
  first: project bootstrap, service accounts and least-privilege IAM, keyless GitHub Actions deploys with
  Workload Identity Federation, Artifact Registry, Cloud Run flags and traffic, Cloud SQL connections and
  pool sizing, Secret Manager, custom domains (load balancer or domain mapping), budgets, and triage of
  deploy, permission, 403 and 503 failures. Examples: "deploy this service to Cloud Run", "set up CI
  without JSON keys", "why does the deploy say actAs denied", "make the backend private", "cut our GCP bill".
triggers:
  - gcp-service-setup
  - gcp
  - cloud run
  - gcloud
  - workload identity
  - cloud sql
---

# gcp-service-setup

An opinionated path for one service on Google Cloud, with the checks and the lessons that cost
something to learn. App-specific facts (project IDs, service names, past incidents) are in
PenguPool memory (`pengupool search`), not here.

**Breadth lives elsewhere.** For any GCP product detail this skill doesn't cover, read Google's own
agent skills at github.com/google/skills (`skills/cloud/`: `gcloud`, `cloud-run-basics`,
`cloud-sql-basics`, `iam-helper-for-troubleshooting`, logging and monitoring skills), and use the
gcloud and Cloud Run MCP servers (github.com/googleapis/gcloud-mcp,
github.com/GoogleCloudPlatform/cloud-run-mcp) as tools when the agent has them. Keep this skill to
the setup path, the checklists and the lessons.

Markers: **(unverified)** = from working knowledge, not confirmed on a Google page; check it before
relying on it.

## Default stack

- One project per environment where budget allows; a shared project with `-dev` services is the
  cheap option, and then prod and dev share quotas and the database's connections.
- A runtime service account per service, predefined roles on the resource. A separate deployer
  account with `roles/run.developer` (or `run.admin`), `artifactregistry.writer` and
  `iam.serviceAccountUser` granted **on the runtime account only**.
- GitHub Actions with Workload Identity Federation (`google-github-actions/auth@v3`,
  `deploy-cloudrun@v3`); no JSON keys anywhere.
- Images in Artifact Registry (`<REGION>-docker.pkg.dev`), immutable tags. Container Registry has
  been shut down for writes since March 2025.
- Cloud Run, request-based billing, `--no-allow-unauthenticated` unless the service is meant to be
  public. Direct VPC egress (Google's recommendation) when it needs the VPC.
- Cloud SQL through `--add-cloudsql-instances` (Unix socket) or a language connector; no public
  authorized networks.
- Secrets in Secret Manager via `--set-secrets`; never `--set-env-vars`.
- gcloud for bootstrap and diagnosis; Terraform (GCS state) for what lives long, once there's more
  than a handful of resources.

## Setup path, in order

1. **Project:** choose a permanent project ID (it ends up in service-account emails, registry
   paths, the SQL connection name and the WIF principal). Link billing, set a budget with alerts,
   enable APIs, check org policies (`gcloud org-policies list --project <PROJECT>`).
2. **Identities:** runtime and deployer accounts as above; never the default compute account.
3. **CI:** WIF pool and OIDC provider with an attribute condition on `repository_owner_id`;
   `workloadIdentityUser` on the deployer account for the `principalSet` of that repository's
   numeric `repository_id`. Numeric IDs survive renames and can't be re-registered.
4. **Registry:** a regional Docker repository with a cleanup policy (dry run first).
5. **Build:** `linux/amd64`, natively where possible; the app listens on `0.0.0.0:$PORT`.
6. **Deploy:** `--service-account`, `--ingress`, `--max-instances` sized to the database's
   connection budget, `--concurrency`, `--set-secrets`; `--no-cpu-throttling` only where work runs
   after the response; `--add-cloudsql-instances` only on services that use the database.
7. **Private services:** `--no-allow-unauthenticated`, `roles/run.invoker` for the caller's
   account, the caller sends an ID token in `X-Serverless-Authorization`.
8. **Data:** Cloud SQL encrypted-only, connector-only, pool sized and released around slow calls.
9. **Ingress:** pick a custom-domain option (below) deliberately.
10. **Verify** (below), then record the rollback revision.

## Decisions to make, not defaults to assume

| Decision | Cheap and simple | Supported and featureful |
| --- | --- | --- |
| Custom domain | Cloud Run domain mapping: no fixed cost. Google lists it as Preview, limited availability and "not production-ready"; no WAF, CDN or static IP | Global external Application Load Balancer + serverless NEG: GA and recommended; Cloud Armor, CDN, IAP, one static IP (free while attached); about $18/mo for the forwarding rule (2026) |
| CPU | Request-based: idle instances cost nothing, but CPU is throttled after the response | Instance-based (`--no-cpu-throttling`): background work runs, billed while the instance lives |
| Cold starts | `--min-instances=0` | `--min-instances=1`: always one warm instance, billed |
| Environments | One project, `-dev` services | A project per environment |

Put both columns to the owner with the dated cost; don't pick one silently. Details in
[references/ingress-and-cost.md](references/ingress-and-cost.md).

## Verify after every deploy or update

```sh
gcloud run services describe <SVC> --region <REGION> --format='yaml(status.traffic,status.url)'
gcloud run services get-iam-policy <SVC> --region <REGION>   # allUsers only on public services
```

A new revision doesn't always take traffic: check `status.traffic`. Then smoke-test `/health`, a
database-backed path, login, and one private service called anonymously (expect 403).

## What only the owner does

Say these plainly; never do them for the owner or ask for a secret value.
1. Create the project and link billing (needs a billing-account role).
2. Put secret values into Secret Manager from their own terminal:
   `printf '%s' "<value>" | gcloud secrets versions add <NAME> --data-file=-`.
3. Approve every change from the Rules in `AGENTS.md`, each with its cost and rollback.

## Reference (read the one that applies)

| When | Read |
| --- | --- |
| Bootstrap, IAM, WIF, Artifact Registry, Cloud Build, CI runners, Terraform | [references/project-and-ci.md](references/project-and-ci.md) |
| Deploy flags, CPU billing, timeouts, long jobs, private services, secrets, traffic, Scheduler, Tasks, Pub/Sub, logs | [references/cloud-run.md](references/cloud-run.md) |
| Cloud SQL: connection options, pool sizing, maintenance, connector-only access | [references/cloud-sql.md](references/cloud-sql.md) |
| Custom domains, certificates and DNS, Cloud Armor, budgets and spending caps | [references/ingress-and-cost.md](references/ingress-and-cost.md) |
| An error message or a failed deploy | [references/troubleshooting.md](references/troubleshooting.md) |

## Every task

1. Search for the owner's rules and earlier work: `pengupool search "<words>"`.
2. Audit read-only: `gcloud config get project`, `gcloud run services list`, `describe`,
   `get-iam-policy`, `gcloud services list --enabled`.
3. Propose the change: the commands or the plan, what it costs, the rollback. Wait for the go.
4. Apply, verify as above, and reply with the evidence. PenguPool records the work; write no log.
