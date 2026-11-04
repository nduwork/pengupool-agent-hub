# Cloud SQL

## Connecting

| Option | Use when |
| --- | --- |
| `--add-cloudsql-instances=<PROJECT>:<REGION>:<INSTANCE>` | Simplest on Cloud Run: Unix socket at `/cloudsql/<PROJECT>:<REGION>:<INSTANCE>` |
| Language connector (Python, Java, Go, Node) | IAM-authorized TLS from code, no sidecar |
| `cloud-sql-proxy` | Laptops, VMs, GKE |
| Private IP (Private Service Access) or Private Service Connect | The database must have no public IP; reach it with Direct VPC egress |

- The runtime account needs `roles/cloudsql.client`, plus `roles/cloudsql.instanceUser` and the
  `cloudsql.iam_authentication` flag for IAM database users (unverified).
- Keep the socket DSN (`host=/cloudsql/…`) in Secret Manager.
- Add `--add-cloudsql-instances` only on services that use the database.

## Connection budget

A small instance has few connections (`db-f1-micro`: about 25, about 20 usable after reserved
ones). Budget = pool size × max instances × services that connect × environments sharing the
instance. Example: pool 4, max instances 1, two services, prod and dev on one instance = 16, under
20. With Cloud Run's default of 100 max instances, one scale-up can exhaust the database for every
environment on it.

## Pool rules

- **Never hold a pooled connection across slow external calls** (an LLM, an HTTP API). Read,
  release, call, reacquire, write. Fan-out workers buffer what they record and write once, instead
  of each opening a connection. Otherwise a handful of concurrent jobs starve the pool and even
  login and health checks return 503.
- **The pool must survive maintenance.** Cloud SQL maintenance is routine. A pool that reserves a
  slot before connecting and doesn't give it back when the connect fails wedges for good: after a
  few failures it reports full while holding no connections, and every request waits out the
  timeout. Return the slot on failure, and test the pool with the database stopped.
- Keep a bounded wait that fails loudly (503 with a clear code). Identical latencies at exactly the
  wait limit are the signature of a wedged pool.

## Lock direct access down

1. `gcloud sql instances patch <INSTANCE> --ssl-mode=ENCRYPTED_ONLY --clear-authorized-networks`
   (old home IPs linger in the list).
2. Connector-only: `gcloud sql instances patch <INSTANCE> --connector-enforcement=REQUIRED`. An
   older SDK without the flag can use the REST API:

   ```sh
   curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H 'Content-Type: application/json' -d '{"settings":{"connectorEnforcement":"REQUIRED"}}' \
     https://sqladmin.googleapis.com/sql/v1beta4/projects/<PROJECT>/instances/<INSTANCE>
   ```

   Leaving `/sql/` out of that path returns a bare 404.
3. Check: the Cloud Run socket and `cloud-sql-proxy` still work; direct TCP to 5432 is refused.

Caveats: an `sslMode` change applies to new connections only; existing plaintext sessions last until
they reconnect or the instance restarts. Every runbook switches to the proxy flow in the same change
(the proxy leg is already TLS, so the client side uses `sslmode=disable`). The proxy needs fresh ADC
(`gcloud auth application-default login`). Rewrite DSNs with a real conninfo parser, never by
string edits, and keep passwords out of argv.

## Sharing an instance

One instance with a database per environment is the cheap start. Prod and dev then share
connections, maintenance windows and noisy-neighbour load; split them when prod matters more than
the instance's cost.
