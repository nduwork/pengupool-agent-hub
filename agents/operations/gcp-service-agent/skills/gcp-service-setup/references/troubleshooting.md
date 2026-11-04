# Troubleshooting

Start read-only: the exact error text, then `gcloud logging read`, `gcloud run services describe`,
`get-iam-policy`, `gcloud services list --enabled`, `gcloud org-policies describe`. For IAM, Google's
Policy Troubleshooter (and the `iam-helper-for-troubleshooting` skill in github.com/google/skills)
says which binding is missing. Propose the smallest fix; apply it only after the owner's go.

| Symptom | Cause | Fix |
| --- | --- | --- |
| `PERMISSION_DENIED: iam.serviceaccounts.actAs` on deploy | Deployer lacks `serviceAccountUser` on the runtime account | Grant it on that account only |
| Deploy auth fails after months of working; "unauthorized" from the auth action | The GitHub repository or org was renamed; the WIF condition or `principalSet` names the old one | Update the condition and binding; bind numeric `repository_owner_id` and `repository_id` |
| `forbidden from accessing the bucket … serviceusage.services.use` | The account submitting the build (the CI deployer) lacks roles | Give it `cloudbuild.builds.editor`, `serviceusage.serviceUsageConsumer` and write access to the source bucket; the build's own account needs `logging.logWriter` and `artifactregistry.writer` |
| `--source` build fails on permissions | The build account lacks registry or storage roles (default changed in 2024, unverified) | Grant `artifactregistry.writer`, `logging.logWriter`, storage; or pass `--build-service-account` |
| `SERVICE_DISABLED`, "API has not been used in project" | API off, or the call bills another project | `gcloud services enable …`; check `gcloud config get project` and the ADC quota project |
| `FAILED_PRECONDITION` adding `allUsers` | Org policy `iam.allowedPolicyMemberDomains` | An org exception, or a load balancer with IAP in front |
| Deploy rejected on ingress | Org policy `run.allowedIngress` | Use an allowed value |
| Create fails on location | Org policy `gcp.resourceLocations` | An allowed region |
| Can't create a service-account key | `iam.disableServiceAccountKeyCreation` | Working as intended: WIF or impersonation |
| "Container failed to start and listen on the port defined by PORT" | Binds 127.0.0.1 or a fixed port; arm64 image; crash at start | Bind `0.0.0.0:$PORT`, build `linux/amd64`, read the revision's logs |
| gcloud rejects a variable "in both" env and secrets | Same name in `--set-env-vars` and `--set-secrets` | Drop it from env vars |
| An env var's value is cut at a comma | `--set-env-vars` splits on commas | `--env-vars-file`, or Secret Manager |
| Change deployed but behaviour unchanged | The new revision has no traffic | `describe --format='yaml(status.traffic)'`; `update-traffic --to-latest` |
| Background job never finishes; progress stalls after the response | CPU throttled between requests | `--no-cpu-throttling` on that service, or move the work to a job or task |
| 502 / "service unavailable" on slow paths only | Gateway timeout shorter than the upstream budget | Align timeouts; add a contract test |
| Browser "Load failed" on long requests though the server finished | Idle connection dropped by a proxy or VPN | Kick off + poll |
| Every request waits exactly N s, then 503, after DB maintenance | Pool leaked slots on failed connects and wedged | Return the slot on connect failure; restart to recover now |
| `db_pool_exhausted` under modest load; login fails too | Connections held across slow calls, or too many instances | Release around slow calls; size `--max-instances` to the budget |
| `RESOURCE_EXHAUSTED` | Regional quota | Quotas page; lower `--max-instances` |
| Direct VPC egress timeouts at startup | Documented connection delay | Startup probe that checks the egress target |
| 403 calling a private service from the gateway | Missing `run.invoker`, wrong audience, or the token in the wrong header | Grant the role; audience = the service URL; `X-Serverless-Authorization` |
| Managed cert stuck PROVISIONING | DNS doesn't resolve to the target yet, or a stale AAAA | Fix DNS, wait 15–60 min |
| Raw 404 from the Cloud SQL Admin API PATCH | `/sql/` missing from the path | `…/sql/v1beta4/projects/<PROJECT>/instances/<INSTANCE>`, or use `gcloud sql instances patch` |
| Laptop can't reach Cloud SQL after lockdown | Connector-only enforcement | `cloud-sql-proxy` with fresh ADC |

Org-policy rows are from working knowledge: the constraint names are standard, their pages were not
re-checked.
