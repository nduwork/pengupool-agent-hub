# Fix patterns by weakness class

Each section: what to look for, the fix, and the check that proves it. Examples are short
Python or TypeScript; translate to the project's language and framework idiom.

## Injection (SQL, NoSQL, shell)

Look for: string formatting, concatenation or template literals that build a query or command;
`shell=True`; `exec`/`system` with interpolated text; Mongo filters taken whole from a body.

Fix: pass values as bound parameters; pass commands as an argument list with no shell.

```python
cur.execute("SELECT * FROM orders WHERE id = %s AND owner_id = %s", (order_id, user.id))
subprocess.run(["git", "log", "--", path], check=True)   # no shell, "--" ends options
```

For a NoSQL filter, build it from typed fields; reject objects where a scalar is expected (an
`{"$ne": null}` password matches everything).

Check: a test that sends `' OR '1'='1`, `; id`, or `{"$ne": null}` and expects a 4xx or no match.

## Cross-site scripting

Look for: `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `|safe`, `Markup()`, markdown
rendered with raw HTML enabled, user data inside `<script>` or event-handler attributes.

Fix: let the framework escape. If HTML must be rendered, run it through an allowlist sanitizer
already in the project (ask before adding one). Add a CSP without `unsafe-inline` for scripts.

Check: store `<img src=x onerror=alert(1)>` and assert the rendered output contains it escaped.

## Access control (IDOR, missing checks)

Look for: handlers that load a record by an id from the request without filtering by the
caller; admin routes guarded only in the UI; mass assignment (`Model(**body)`) that lets a
caller set `role` or `owner_id`.

Fix: scope every lookup by the caller (`WHERE id = ? AND owner_id = ?`), or load and then
check a policy function; return 404 rather than 403 when existence itself is sensitive. Build
models from an allowlist of writable fields.

Check: two users; B requests A's resource and gets 404; B's update body with `role=admin` is
ignored.

## Schema validation at the boundary

Parse once at the entry point into a typed value (pydantic, zod, JSON Schema, the framework's
validator): allowed fields only, types, lengths, ranges, enums, formats. Reject with 4xx and a
structured error. Downstream code uses only the parsed value, never the raw body.

Check: oversize string, wrong type, extra field, missing field each give a 4xx.

## File uploads

Allowlist content types; cap size before reading the whole body; verify magic bytes when type
matters; generate the stored name yourself; store outside the web root or in object storage;
serve with `Content-Disposition: attachment` and the right type. The extension proves nothing.

Check: a 2x-over-limit file is rejected; an HTML file renamed `.png` is rejected or served as a
download.

## Server-side request forgery

Any URL the caller influences (webhooks, import from URL, previews, image proxies).

Fix: allow only `https` (and `http` if needed) and an explicit host allowlist when you can.
Otherwise resolve the host, reject if **any** address is loopback, private, link-local
(including `169.254.169.254`), unique-local or reserved, for IPv4 and IPv6; connect to the
address you checked; turn off redirects; cap response size and time.

Check: `http://127.0.0.1/`, `http://[::1]/`, `http://169.254.169.254/`, a hostname resolving to
a private address, and a redirect to one are all refused.

## Destructive operations on derived paths

A delete, move or overwrite is only as safe as the value naming its target. Before acting,
require all of: the real path (symlinks resolved) is under an allowlisted root; it is at least
one level below that root; and ownership evidence (a marker, a database row) was read before the
operation. On refusal, log and stop; never fall back to a broader path.

```python
real = os.path.realpath(target)
root = os.path.realpath(ALLOWED_ROOT)
if os.path.commonpath([real, root]) != root or real == root:
    raise PermissionError(f"refusing {real!r}")
```

Check: `../`, an absolute path, a symlink pointing outside, and the root itself are refused.

## Unsafe deserialization

Look for `pickle.load`, `yaml.load` without a safe loader, Java/PHP native deserialization, or
`eval` on data. Fix: a data-only format and a schema (`json`, `yaml.safe_load`).

## Sensitive data in responses and logs

Serialize responses from an explicit field list. Log identifiers, not payloads; never log
passwords, tokens, full card numbers or personal data. Errors returned to callers carry a short
message and a correlation id; detail goes to the server log.

## Model (LLM) output

Never pass it into `eval`, SQL, a shell, raw HTML or a file path. Parse into a schema, validate
every tool argument as if a stranger typed it, confirm destructive tool calls, cap tokens and
recursion. Content the model read (pages, files, emails) may contain instructions; enforce
permissions in code.

## Rate limiting and resource caps

Strict limits on login, password reset, signup and token endpoints; general limits elsewhere.
Use a shared store (Redis, the database) when there is more than one instance; in-memory
counters multiply by instance count. Cap request body size, pagination size and timeouts.

Check: the N+1th login attempt within the window returns 429.
