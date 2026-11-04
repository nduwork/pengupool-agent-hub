# Authentication, sessions and authorization

Prefer the framework's or identity provider's built-in mechanism over hand-written auth. Most
findings here are a missing flag or a missing check, not a missing system.

## Passwords

- Hash with argon2id, scrypt or bcrypt (cost tuned so one hash takes roughly 100-300 ms on the
  server). Never a fast hash (MD5, SHA-*) and never reversible encryption.
- Compare secrets with a constant-time function.
- Length over complexity rules: allow long passphrases; reject known-breached passwords if the
  project already has a way to check.
- Login and reset failures return the same message whether or not the account exists.

## Sessions (server-side)

- Session id is random (128+ bits), stored in a cookie with `HttpOnly`, `Secure`,
  `SameSite=Lax` (or `Strict`), a bounded lifetime and an idle timeout.
- Issue a new session id at login and at any privilege change (stops session fixation).
- Logout deletes the session on the server, not only the cookie.
- State-changing requests with cookie auth need CSRF protection: SameSite plus a token or an
  origin check for anything `SameSite` does not cover.

## Tokens (JWT and similar)

- Access tokens are short-lived (minutes); refresh tokens are long-lived, stored server-side or
  hashed, rotated on every use, and revoked on reuse.
- Verify signature, algorithm (pin it; reject `none` and unexpected algorithms), issuer,
  audience and expiry on every request.
- Do not put secrets or personal data in the payload; it is only encoded, not encrypted.
- In a browser, keep tokens in `HttpOnly` cookies rather than `localStorage`, where any XSS can
  read them.
- Signing keys come from the secret store and have a rotation plan (key ids, overlap window).

## OAuth 2 / OpenID Connect

- Authorization code flow with PKCE; never the implicit flow.
- Validate `state` (CSRF) and `nonce` (replay); exact-match redirect URIs, no wildcards.
- Validate the ID token like any JWT; map identity by issuer + subject, not by email alone.
- Request the smallest scopes the feature needs.

## Password reset and email links

Single-use, random, stored hashed, short expiry (an hour or less), invalidated after use and
after a password change. Reset invalidates existing sessions.

## Multi-factor

Offer it for admins at least. Rate-limit code entry; recovery codes are single-use and hashed.

## Authorization models

- **Role-based**: users have roles, roles grant permissions; check the permission, not the role
  name, at the call site so roles can change without code edits.
- **Ownership / relationship**: the record's owner or tenant must match the caller. Enforce it in
  the query or in one policy function every handler calls.
- **Multi-tenant**: every query carries the tenant filter; prefer a default scope or row-level
  security so a forgotten filter fails closed.
- Deny by default: a route with no policy is a finding.

## Audit checklist

- [ ] Every protected route authenticates on the server.
- [ ] Every resource access checks the caller's right to *that* resource.
- [ ] Writable fields come from an allowlist (no setting `role`, `owner_id`, `is_admin`).
- [ ] Password hashing uses a slow, salted algorithm.
- [ ] Session/token lifetimes are bounded; logout and reset revoke server-side.
- [ ] Cookies have `HttpOnly`, `Secure`, `SameSite`; CSRF covered for cookie auth.
- [ ] JWT algorithm pinned; `aud`, `iss`, `exp` checked.
- [ ] Login, reset and MFA endpoints are rate-limited.
- [ ] Security events (login, failure, permission change) are logged without secrets.
