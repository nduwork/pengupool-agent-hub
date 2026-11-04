# Launch checklist template

Copy, drop the sections that do not apply, and fill every kept line with its evidence or the
reason it is open. "Owner runs" marks a step only the owner performs.

```markdown
## Launch: <service or release>  —  <date>
Risk: <routine | notable | high> because <reason>
Owner deploying: <role, not a personal name if the write-up leaves the team>

### Ready to build
- [ ] CI green on the release commit — <run link>
- [ ] Reviewed and approved — <PR link>
- [ ] No known critical bugs in the release — <query or tracker filter used>
- [ ] Lint, type check and dependency audit clean, or exceptions listed

### Safe to run
- [ ] New config and secrets exist in the target environment (names only, never values)
- [ ] Inputs from users validated; auth checks on new endpoints
- [ ] Health check endpoint covers the new path
- [ ] Error handling covers the expected failures of new outside calls

### Data
- [ ] Migration applied and rolled back on a copy of production-sized data — <command, time taken>
- [ ] Migration is additive, or the destructive step ships in a later, separate deploy
- [ ] Large backfills run in throttled batches, off the request path

### Flags
- [ ] Flag exists, defaults off, has an owner and a removal date
- [ ] Both flag states tested in CI
- [ ] No flag nested inside another

### Watching
- [ ] Dashboards show error rate, p95 latency and traffic for the touched paths
- [ ] Alerts exist for the user-facing symptoms (see instrument-service)
- [ ] Baseline numbers recorded before the deploy — <values>
- [ ] Advance / hold / roll back thresholds agreed — <table>
- [ ] Someone is watching for the first hour — <rotation or role>

### Rollback
- [ ] Undo for each step written with its command and expected time
- [ ] Rollback path tried in staging, or why it cannot be
- [ ] Plan for data written by the new version

### Tell people
- [ ] On-call and affected teams told of the window
- [ ] Breaking API change: consumers told, with dates and a migration note
- [ ] Docs, runbooks and changelog updated

### Steps (owner runs)
1. <command>  — check: <how to see it worked>  — undo: <command>
2. ...

### After
- [ ] Health, errors and latency within thresholds after the agreed window
- [ ] Key user flow checked by hand
- [ ] Release notes sent, tickets closed, flag removal scheduled
```

## Timing

Prefer a window when the people who can roll back are present and alert. A high-risk launch
right before people leave for the day or the weekend is a finding worth naming.
