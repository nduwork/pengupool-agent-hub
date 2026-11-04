# Project, identities and CI

Placeholders: `<PROJECT>`, `<PROJECT_NUMBER>`, `<REGION>`, `<SVC>`, `<RUNTIME_SA>`,
`<DEPLOYER_SA>`, `<GH_OWNER_ID>`, `<GH_REPO>` (owner/name), `<GH_REPO_ID>`.

## Project

- **The project ID is permanent in practice.** It becomes part of service-account emails, registry
  paths, secret references, the Cloud SQL connection name and the WIF principal. Use a codename the
  owner can live with; keep product branding out of infrastructure names.
- Link billing, then set a budget with alert thresholds (50/90/100 %) and a Pub/Sub topic if a
  function should act on it. A budget only notifies (see ingress-and-cost.md › Budgets).
- `gcloud auth application-default set-quota-project <PROJECT>` so local ADC calls bill and quota
  against the right project.
- Enable only what's used: `run`, `artifactregistry`, `iam`, `iamcredentials`, `sts`,
  `secretmanager`, `sqladmin`; `compute` and `certificatemanager` for a load balancer;
  `cloudbuild` for Cloud Build; `cloudscheduler`, `cloudtasks` for jobs.
- In an organization, read the org policies before designing: `iam.allowedPolicyMemberDomains`
  blocks `allUsers`, `run.allowedIngress` limits ingress values, `gcp.resourceLocations` limits
  regions, `iam.disableServiceAccountKeyCreation` blocks keys (on by default for new orgs since
  2024, unverified).

## Service accounts and IAM

| Do | Don't |
| --- | --- |
| One runtime account per service, `--service-account` on deploy | Run on the default compute account (it often holds Editor) |
| Predefined roles on the resource: `cloudsql.client`, `secretmanager.secretAccessor` on each secret | Owner, Editor, Viewer; project-wide secret access |
| Deployer: `run.developer` (or `run.admin` if it sets IAM on services), `artifactregistry.writer`, `iam.serviceAccountUser` **on the runtime account** | `serviceAccountUser` at project level (it can act as every account) |
| IAM conditions for time-boxed grants | Long-lived broad grants to people |

```sh
gcloud iam service-accounts add-iam-policy-binding <RUNTIME_SA> \
  --member=serviceAccount:<DEPLOYER_SA> --role=roles/iam.serviceAccountUser
```

Grants a deploy needs every time (such as `run.invoker` from a gateway to a private service) can be
re-applied idempotently by the deploy job.

## Workload Identity Federation for GitHub Actions

```sh
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-oidc --location=global \
  --workload-identity-pool=github --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id" \
  --attribute-condition="assertion.repository_owner_id=='<GH_OWNER_ID>'"
gcloud iam service-accounts add-iam-policy-binding <DEPLOYER_SA> --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/attribute.repository_id/<GH_REPO_ID>"
```

```yaml
permissions: { id-token: write, contents: read }
concurrency: { group: deploy-${{ github.ref }}, cancel-in-progress: true }  # revisions are atomic
steps:
  - uses: google-github-actions/auth@v3
    with:
      workload_identity_provider: projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/providers/github-oidc
      service_account: <DEPLOYER_SA>
  - uses: google-github-actions/deploy-cloudrun@v3
```

- **Always set an attribute condition**; without one any GitHub repository can reach the pool.
  Google requires one for GitHub providers (unverified).
- **Bind numeric IDs, not names.** A condition or `principalSet` that names the repository
  (`attribute.repository/<GH_REPO>`) breaks silently when the repository or org is renamed: the
  token stops matching and the deploy fails with an unhelpful auth error. Worse, a deleted name can
  be re-registered by someone else. The numeric `repository_owner_id` and `repository_id`
  (`gh api repos/<GH_REPO> --jq '.owner.id, .id'`) survive renames and can't be reused. Still
  re-test WIF after any rename, and alert on failed deploys instead of discovering them weeks later.
- Prod deploys run on an explicit release event (a tag or a release), not every push to main.
- Older guides use `@v2` of the actions; v3 is current (2026-11).

## Artifact Registry

```sh
gcloud artifacts repositories create app --repository-format=docker --location=<REGION>
gcloud auth configure-docker <REGION>-docker.pkg.dev
gcloud artifacts repositories set-cleanup-policies app --location=<REGION> --policy=cleanup.json --dry-run
```

Tags are immutable (commit SHA or release version); never move one. The cleanup-policy JSON shape
is unverified: run with `--dry-run` and read the result first.

## Building images

- Build `linux/amd64`. An arm64 image fails at start ("failed to start and listen on the port").
  Building amd64 on an Apple-silicon Mac runs under emulation: slow and occasionally flaky.
- **A self-hosted Mac runner that builds with Docker Desktop is fragile:** Docker Desktop doesn't
  start after a reboot or in a non-interactive session. Prefer Cloud Build or a Linux runner; keep
  the deploy path off GUI apps on unattended Macs.
- **Cloud Build needs more IAM than you expect, for two identities.** Whoever submits the build
  (the CI deployer account) needs `cloudbuild.builds.editor`, `serviceusage.serviceUsageConsumer`
  and write access to the source bucket; missing one gives "forbidden from accessing the bucket …
  serviceusage.services.use". The build's own service account needs `logging.logWriter`,
  `artifactregistry.writer` and read access to the source bucket. Grant and test all of them
  before switching the pipeline over.
- `gcloud run deploy --source` builds with Cloud Build and buildpacks: fine for prototypes; CI
  deploys an immutable image.

## gcloud or Terraform

| Use | For |
| --- | --- |
| gcloud | Bootstrap (state bucket, first accounts), one-off diagnosis, CI deploying a new image |
| Terraform (`hashicorp/google`, `google-beta`) | Everything long-lived: projects, IAM, registry, service shape, SQL, secrets, schedulers |

- State in GCS: `backend "gcs" { bucket = "<PROJECT>-tfstate", prefix = "<SVC>/prod" }`, with
  versioning and uniform access on the bucket (unverified).
- Modules: `terraform-google-modules/project-factory`, `github-actions-runners//modules/gh-oidc`
  (WIF), Cloud Foundation Fabric. Infrastructure Manager runs Terraform as a Google-managed service.
- Avoid split-brain when Terraform owns the service and CI changes the image:
  `lifecycle { ignore_changes = [template[0].containers[0].image] }` (unverified).
- A hand-built setup (gcloud only) needs a runbook that lists every resource and the command that
  made it; that runbook is what makes a restore possible.
