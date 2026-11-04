# Cloud Run

## Deploy flags

```sh
gcloud run deploy <SVC> --image=<REGION>-docker.pkg.dev/<PROJECT>/app/<SVC>:<SHA> --region=<REGION> \
  --service-account=<RUNTIME_SA> --no-allow-unauthenticated \
  --min-instances=0 --max-instances=<N> --concurrency=<C> \
  --set-secrets=DB_URL=db-url:3 --add-cloudsql-instances=<PROJECT>:<REGION>:<INSTANCE>
```

- **`--max-instances` defaults to 100.** Size it from the database: pool size × max instances ×
  services × environments must stay under `max_connections` minus headroom (see cloud-sql.md).
  Services that hold no pool (a gateway) can scale freely. Raise the cap together with the database
  tier, never alone.
- `--ingress`: `all`, `internal`, or `internal-and-cloud-load-balancing` (only reachable through a
  load balancer). Changing ingress model (dropping or adding a load balancer) means changing this on
  every service; check deploy defaults don't drift from what's live.
- Canary: `--no-traffic --tag=canary`, test the tag URL, then
  `gcloud run services update-traffic <SVC> --to-tags=canary=10`, then `--to-latest`.
- Direct VPC egress (`--network`, `--subnet`, `--vpc-egress=private-ranges-only`) is Google's
  recommendation over Serverless VPC Access connectors. Its connection can take a minute or more at
  startup: add an HTTP startup probe that checks the egress target.

## CPU allocation and background work

- **Request-based billing throttles CPU to near zero between requests.** Work a thread keeps doing
  after the response is sent (ingest, generation, cleanup) freezes and never finishes.
- `--no-cpu-throttling` (instance-based billing) fixes it and costs more: set it only on the
  services that run work after the response.
- Better still for long work: Cloud Run jobs, or Cloud Tasks calling a handler.

## Long requests and timeouts

- **Don't hold an idle HTTP request open for long.** Proxies and VPNs drop connections that carry no
  bytes for 100+ seconds; streaming (SSE) through Cloud Run plus a gateway proved unreliable. For a
  job longer than about 30 seconds: a POST that returns a job id, a worker that does the job, and
  short GET polls.
- **Keep timeouts consistent across layers:** browser deadline ≥ gateway proxy timeout ≥ upstream
  budget (for example an LLM call of 60–90 s). A gateway's 30 s default under a 90 s upstream budget
  shows users a false "service unavailable" (502). When the timeouts live in different files or
  languages, pin them together with a contract test.
- Cloud Run's own request timeout (`--timeout`, up to 60 min) must exceed the longest of them.

## Private services: IAM between services

Make only the gateway public; the rest IAM-only. No VPC needed.
1. `--no-allow-unauthenticated` on the private services.
2. `gcloud run services add-iam-policy-binding <PRIVATE> --member=serviceAccount:<GATEWAY_SA>
   --role=roles/run.invoker` (safe to re-apply on every deploy).
3. The gateway mints an ID token from the metadata server with audience = the private service's
   URL, caches it for about 55 minutes, and sends it in **`X-Serverless-Authorization`**. Cloud Run
   checks that header and leaves the app's own `Authorization` header (a user's session token)
   untouched.
4. The gateway strips any `X-Serverless-Authorization` a client sends, and skips minting when run
   locally.

Roll out in this order: token minting first, then any domain change, then flip IAM. No outage
window.

## Secrets

```sh
gcloud secrets add-iam-policy-binding <NAME> --member=serviceAccount:<RUNTIME_SA> \
  --role=roles/secretmanager.secretAccessor
gcloud run deploy <SVC> --set-secrets=DB_PASS=<NAME>:3            # env var, pinned version
gcloud run deploy <SVC> --set-secrets=/secrets/db=<NAME>:latest   # file, read at access time
```

- **Never `--set-env-vars` for a secret:** env vars are stored in the revision spec, readable by
  anyone with `run.viewer`.
- gcloud rejects a variable named in both `--set-env-vars` and `--set-secrets`: a deploy script that
  always injects a key as an env var breaks the day that key moves to Secret Manager. Skip keys the
  secret bindings already provide.
- A comma inside an `--set-env-vars` value silently splits the list. Fail loudly on commas, or use
  `--env-vars-file`.
- Env-var secrets resolve when an instance starts: pin a version and redeploy to rotate. A mounted
  file with `latest` picks up new versions (unverified).

## Dev-only surfaces

Close what is for local use only. Cloud Run sets `K_SERVICE`; when it's set, return 404 for API
docs (`/docs`, `/redoc`, `/openapi.json`), debug routes and admin consoles. A public docs page hands
scanners the full route inventory, admin and billing routes included.

## A gateway that allowlists paths

The public gateway proxies only known path prefixes (webhooks included) and returns 404 for the
rest. Scanner traffic then never wakes a paid, always-on backend.

## Traffic after an update

`gcloud run services update` (secrets, env, flags) creates a revision, which doesn't always take
traffic (for example when traffic is pinned to a revision). Check every time:

```sh
gcloud run services describe <SVC> --region <REGION> --format='yaml(status.traffic)'
```

## Scheduler, Tasks, Pub/Sub

All call Cloud Run with an OIDC token from an invoker account that holds `run.invoker`.

```sh
gcloud scheduler jobs create http nightly --schedule="0 3 * * *" --uri=<URL>/jobs/nightly \
  --http-method=POST --oidc-service-account-email=<INVOKER_SA> --location=<REGION>
gcloud tasks queues create work --location=<REGION> --max-attempts=5 --min-backoff=10s
gcloud pubsub subscriptions create <SVC>-push --topic=events --push-endpoint=<URL>/pubsub \
  --push-auth-service-account=<INVOKER_SA> --ack-deadline=60
```

Delivery is at least once: handlers are idempotent and return 2xx only when done. Add a dead-letter
topic on Pub/Sub. A cron in GitHub Actions is fine for one light job; Scheduler is the supported
path.

## Logs

One JSON object per line on stdout with `severity`, `message`, and
`logging.googleapis.com/trace` = `projects/<PROJECT>/traces/<TRACE_ID>` so logs join their trace
(unverified). Alert on 5xx ratio, p95 latency and instance count; add an uptime check on the public
URL.
