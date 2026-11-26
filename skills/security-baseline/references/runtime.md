# Build, runtime and local development

Each item states the baseline, then how to check it. Grep finds candidates. Read the code
before recording, because a match in a test or a dead path is not a finding.

## Secrets

- **Secrets reach the process at runtime**, from a secret manager or the environment the
  platform injects. Required config fails at boot when it's missing instead of falling back to a
  default. Look at the config loader (`runtime.exs`, `config.go`, `settings.py`, `env.ts`) for
  defaults on secret keys.
- **Nothing secret is committed.** `.gitignore` covers `.env*` (templates aside), `secrets/`,
  key and certificate files, tfstate, `*.tfvars` that hold values, and local tool config
  (`mise.local.toml`, `.claude/settings.local.json`). Only the repo's own ignore files count: a
  rule in your global git ignore doesn't protect anyone else's clone or CI. Check what is tracked
  by name only:
  ```bash
  git ls-files | grep -iE '(^|/)\.env($|\.)|secrets/|\.(pem|key|p12|pfx|tfstate)$|credentials.*\.json|service-account.*\.json|-key\.json$' \
    | grep -vE '\.env\.(example|sample|template|tmpl)$'
  ```
  Read `.env.example` and similar templates only to confirm the values are placeholders.
- **Nothing secret lies readable on disk in the working tree.** Find world-readable files with
  secret-looking names from the repo root. A direct `ls` or `stat` on `secrets/` may be refused
  by the session's own deny rules, which is the rule working as intended.
  ```bash
  find . \( -path ./.git -o -path ./.jj -o -path ./node_modules \) -prune -o -type f -perm -004 -print \
    | grep -iE 'secrets/|dumps/|\.(pem|key|p12|pfx|tfstate)$|credentials.*\.json|service-account.*\.json|-key\.json$|(^|/)\.env($|\.)' \
    | grep -vE '\.env\.(example|sample|template|tmpl)$'
  ```
  A world-readable key file is high: stop and tell the user.
- **No secrets in images**: no `ARG`/`ENV` with secret values in Dockerfiles, and no `COPY` of
  `.env` or key files. Build secrets go through `--mount=type=secret`.
- **No customer production data on disk**: `dumps/`, `*.sql`/`*.dump`/`*.bak` files over a few
  MB, CSV exports. Check names and sizes, never contents. Any hit means stop and tell the user.

## Containers

- **Non-root**: every final image stage sets `USER` to a non-root user, and k8s and Helm set
  `runAsNonRoot: true`. Distroless images have a `:nonroot` tag.
- **Multi-stage**, so compilers and build secrets stay out of the shipped image.
- **Where cheap**, set `readOnlyRootFilesystem` and drop capabilities.

## Identity and authorization

- **Deny by default.** The auth middleware rejects anything not explicitly allowed, and a test
  fails when an endpoint, RPC method or route is left unclassified. If there is no such test,
  record its absence (medium): without it the next endpoint ships open by accident.
- **Tenancy enforced below the handler.** Row-level security (Postgres RLS with `FORCE`), or a
  policy layer the ORM can't bypass, plus a CI check that fails when a table lacks it.
  `grep -rn 'ENABLE ROW LEVEL SECURITY'` against the tenant-scoped tables.
- **Identity from a verified credential, never from client input**: no tenant or user ID read
  from a body field, query parameter or client-settable header.
- **Tokens verified in the service**, even behind a gateway or mesh. High when nothing in the
  repo documents a verifying proxy in front; medium when one does. Verify the signature with pinned
  algorithms, `iss`, `aud`, `exp`. Flag `UnsafeClaimsWithoutVerification`, `ParseUnverified`,
  `jwt.decode(..., options={"verify_signature": False})`, `verify=False`, `algorithms` left
  open. Trust a header set by a proxy only where the repo documents that boundary and the edge
  overwrites the header.
- **Unknown principals get nothing.** No sentinel IDs (`0`, `*`, `NULL`) that a policy reads as
  "all tenants", and no fallback identity for a user missing from the database. Check what the
  auth code does on "not found", and what the RLS policies do with the default value.
- **Internal-call shortcuts are real secrets.** A marker or shared token that skips authz is
  generated, stored as a secret and rotated, never a constant in the code.

## Errors, logs and telemetry

- **Clients get generic errors**; details go to logs. Flag `err.Error()`, `str(e)` and stack
  traces in response bodies.
- **No tokens, PII or query strings in logs, traces and error reports**: parameter filtering
  (`filter_parameters`), scrubbing in Sentry `beforeSend` (and `sendDefaultPii` off), OTEL
  attribute processors, and access logs without query strings when tokens travel there.

## Transport and outbound calls

- **Verification never disabled**: `InsecureSkipVerify`, `InsecureIgnoreHostKey`,
  `verify=False`, `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED`. Each one is
  high, except in test code.
- **Every outbound client has a timeout.** Go's `http.Client{}` and `http.Get` have none,
  Python `requests` has none, and Node `fetch` has none without an `AbortSignal`.

## Web surface

The baseline here is the platform's secure defaults, actually switched on:
- CSP enforced, not report-only.
- HSTS.
- Cookies `Secure`, `HttpOnly` and `SameSite`, and session cookies encrypted where the framework
  supports it.
- CSRF protection on every browser pipeline.
- CORS never `*` together with credentials.
- Rate limits on authentication and other costly endpoints.
- gRPC or GraphQL reflection and introspection off in production.

## Local development

- **Bound to loopback.** In compose, `"127.0.0.1:5432:5432"`, not `"5432:5432"`, which
  publishes to every interface, including the coffee-shop Wi-Fi. The same goes for dev servers
  (`--host 0.0.0.0`, env flags like `BIND_ALL`) and local databases (`listen_addresses`).
  ```bash
  find . -maxdepth 3 -name '*compose*.y*ml' -not -path './node_modules/*' -exec grep -HnE '^\s*-\s*"?[0-9]+:[0-9]+' {} +
  ```
- **Default credentials only behind loopback.** `postgres/postgres` is fine on 127.0.0.1 and
  high on all interfaces.

## Infrastructure as code (when present)

The baseline only, not a cloud audit:
- No wildcard actions or resources in IAM granted to CI or workloads.
- No broad roles (owner, editor, admin) on CI identities.
- No public buckets, and no `0.0.0.0/0` ingress except to a load balancer.
- A remote state backend with encryption, versioning and locking.
- Deletion protection on production data stores.
- Secrets created as placeholders with values set out of band, so they never land in state.
