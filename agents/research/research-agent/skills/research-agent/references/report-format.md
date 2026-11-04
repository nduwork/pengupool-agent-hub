# Report format

The report you send back to whoever asked. Keep it skimmable; the answer goes first.

---

```markdown
# <Title>

- **Request**: <request_id or one line>
- **Requester**: <session name/id>
- **Date**: <YYYY-MM-DD>
- **Status**: DONE | PARTIAL | BLOCKED
- **Confidence**: High | Medium | Low — <one line why>
- **Access scope**: public | requester-private (unknown ⇒ requester-private). Use the **most restrictive of all inputs** — request, requester context, cited sources, and conclusions.

## TL;DR
<The answer in 1–3 sentences, recommendation included.>

## Recommendation
<What to do next, and what would change this recommendation.>

## Findings

### Q1 — <question>
- <claim> — **<confidence>** — <source: `path:line` / URL (accessed YYYY-MM-DD) / command output>
- <claim> — **<confidence>** — <source>

### Q2 — <question>
…

## Options matrix          (omit when no choice is involved)

| Option | <criterion 1> | <criterion 2> | <criterion 3> | Notes |
| --- | --- | --- | --- | --- |
| A | | | | |
| B | | | | |

## Open questions / unknowns
- <what could not be verified, and what would settle it>

## Next actions
- [ ] <action> — owner: <who>
- [ ] <action> — owner: <who>

## Provenance
- Commands: `<command>` → <result>
- Files: `<path:line>`
- URLs: <URL> (accessed YYYY-MM-DD)
```
