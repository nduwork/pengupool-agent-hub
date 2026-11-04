# Ingress, domains and cost

## Custom domain: a trade-off for the owner

| | Domain mapping | Global external Application Load Balancer + serverless NEG |
| --- | --- | --- |
| Status | Preview, limited availability; Google: "not production-ready" | GA, Google's recommended option |
| Fixed cost | None | Forwarding rule about $18/mo (2026). A static IP attached to a forwarding rule is free; URL map, proxy, NEGs and backend services cost nothing while idle |
| DNS | CNAME to `ghs.googlehosted.com` (or Google's A/AAAA records at the apex) | A/AAAA records to the load balancer's IP |
| Features | TLS cert, nothing else | Cloud Armor (WAF, rate limits), CDN, IAP, one static IP, path fan-out to several services |
| Service ingress | `all` | `internal-and-cloud-load-balancing` |

Domain mapping has run fine for low-traffic apps and saves the fixed cost; the load balancer is the
supported path and the only one with a WAF. Put both to the owner with the dated cost and the
traffic level; record which was chosen and why.

Moving from a load balancer to domain mappings cheaply and reversibly:
- Delete the forwarding rule (the costed part). Keep the URL map, target proxy, NEGs, backend
  services and certs dormant, and write the restore runbook.
- The static IP: once detached, a reserved IP costs about $7/mo (2026). Keeping it means a restore
  reuses the same IP, with no DNS change and no cert re-provisioning. Releasing it saves that, and
  a restore then gets a **new IP**: DNS changes again and managed certs re-provision after DNS
  points back. Another choice for the owner.
- Change every service's `--ingress` to match, and the deploy workflow's defaults too, or the next
  deploy cuts the service off.
- Map an API hostname to the gateway, not straight to a backend, so webhook URLs stay the same.

## Certificates and DNS

- An A record to the load balancer's IP routes through it; a CNAME to `ghs.googlehosted.com` is a
  domain mapping and **bypasses the load balancer and Cloud Armor**.
- A Google-managed certificate's domain list can't be changed after creation: create a second one
  and attach both. The attach command **replaces** the list, so name every certificate in it.
- Certs go ACTIVE only after DNS resolves to the right target: 15–60 minutes.
- Lower DNS TTLs a day before a cutover. Delete stale AAAA and parking records; a leftover AAAA
  sends part of the traffic elsewhere.
- Add every serving hostname to the auth provider's authorized domains.

## Cloud Armor

Turn it on when traffic or abuse justifies it (about $10–15/mo in 2026). Start the OWASP rules with
`--preview` and read the logs before enforcing; for abuse, `rate-based-ban` with
`--enforce-on-key IP`. Detaching a policy doesn't stop its charges: delete it.

## Budgets and spending caps

- **A budget alert is not a cap.** It only notifies.
- A hard stop is a function subscribed to the budget's Pub/Sub topic that detaches billing from the
  project. That stops every service, Cloud SQL included, until someone re-links billing by hand,
  and recovery isn't guaranteed: Google's tutorial for it
  (cloud.google.com/billing/docs/how-to/disable-billing-with-notifications) warns that "resources
  might be irretrievably deleted" and gives "no guarantee of service recovery". With a database on
  the project, that's possible data loss. Tell the owner that in those words before they agree;
  agree its scope, test it on a sandbox project, have it act on the host project last, and keep
  backups outside the project.

## Fixed-cost checklist (low traffic)

- Load balancer forwarding rule and reserved IP: needed, or can domain mapping do for now?
- `--min-instances` above 0 and `--no-cpu-throttling`: only where needed.
- Cloud SQL tier and a second instance: one small instance with a database per environment is the
  cheap start.
- Cloud Armor policies that exist but aren't needed.
- Artifact Registry without a cleanup policy keeps growing.
