# CI, supply chain and repo settings

Each item states the baseline, then how to check it. Paths assume GitHub Actions; for another CI,
check the same property in its config.

## Workflows

**Actions pinned to a full commit SHA**, with a `# vX.Y.Z` comment so updates stay readable.
A tag can be moved to malicious code after you trust it; a SHA can't.
```bash
grep -rnE '^\s*-?\s*uses:\s*[^ ./][^ ]*@' .github/ | grep -vE '@[0-9a-f]{40}\b'
```
Local actions (`./…`) and `docker://…@sha256:` are fine. Medium; high in a job that holds any
secret or `id-token: write`, since that's what a moved tag would take.

**Least-privilege token.** Every workflow sets top-level `permissions:` (usually
`contents: read`), and jobs widen only what they need. Without it the token gets the repo
default, often write.
```bash
for f in .github/workflows/*.y*ml; do grep -q '^permissions:' "$f" || echo "no top-level permissions: $f"; done
```

**No PR code with secrets.** `pull_request_target` and `workflow_run` run with the base repo's
secrets; checking out or building the PR head in them hands those secrets to any fork. High.
```bash
grep -lnE 'pull_request_target|workflow_run' .github/workflows/* | xargs grep -nE 'head\.(sha|ref)|github\.head_ref|refs/pull'
```

**No script injection.** `${{ github.event.* }}`, `${{ inputs.* }}` and `github.head_ref`
expand into the shell before it runs, so a crafted PR title or branch name becomes code. Pass
them through `env:` instead. Grep finds one-liners; read multi-line `run: |` blocks too.
```bash
grep -rnE '\$\{\{\s*(github\.event\.|inputs\.|github\.head_ref)' .github/workflows/
```
High in a job with secrets or `id-token: write`, medium otherwise.

**Comment-triggered jobs check who commented.** `issue_comment` and `pull_request_review_comment`
jobs (`/deploy`, `@claude`) gate on `author_association` (OWNER, MEMBER, COLLABORATOR) before
doing anything privileged.

**Keyless cloud access.** CI reaches the cloud through OIDC (`id-token: write` with
`role-to-assume` or `workload_identity_provider`), never stored keys. Flag
`secrets.*ACCESS_KEY*`, `credentials_json:`, `*_SA_KEY`, `service_account_key`. Where the trust
policy lives in the repo's IaC, check it pins the repo plus a branch or environment (the `sub`
or `attribute.ref` condition); repo-wide trust lets any branch or PR workflow assume the role.
Plans run as a read-only identity; applies run only from a protected environment.

## Pins and installs

- **Images by digest**: `FROM image:tag@sha256:…`, and the same in compose, Helm values and k8s
  manifests. No `latest`, no untagged image. `grep -rnE '^FROM ' --include='Dockerfile*' .`
- **Tools by exact version** in `mise.toml`, `.tool-versions` and CI setup actions: no `latest`.
- **Lockfile installs in CI**: `npm ci`, `pnpm install --frozen-lockfile`,
  `bun install --frozen-lockfile`, `yarn --immutable`, `go mod download` with a committed
  `go.sum`, `mix deps.get` with a committed `mix.lock`, `uv sync --locked`. A plain
  `npm install` or `bun install` in CI rewrites the lockfile from whatever the registry serves.
- **No dependencies from git branches or unpinned URLs** in manifests (`github:owner/repo`,
  `git+https://…` without a commit).
- **Updates are automated**: Dependabot or Renovate covers every ecosystem present, including
  `github-actions` and `docker`, so SHA and digest pins don't rot. A cooldown of a few days
  keeps a freshly compromised release from landing the same hour.

## Scanning

- **Secrets**: gitleaks or trufflehog in CI or a pre-commit hook, and GitHub secret scanning
  with push protection where the plan has it. For the history itself, run
  `gitleaks git --redact --no-banner` and report the count and rule IDs only.
- **Dependencies**: the ecosystem's audit in CI: `govulncheck`, `npm`/`pnpm`/`bun audit`,
  `mix_audit` and `mix hex.audit`, `pip-audit`, `cargo audit`, plus an image scanner (trivy,
  grype) when the repo ships images.
- **Static analysis where cheap**: `gosec` through golangci-lint, `sobelow` for Phoenix,
  `bandit`, semgrep or CodeQL, and an IaC scanner (trivy config, checkov, tflint) for IaC.
- **Ignore files are justified**: every entry in `.trivyignore`, `.gitleaksignore`,
  `.mix_audit.ignore`, `.snyk` and the like carries a reason and a revisit date or condition.
  An ignore without one is a permanent hole that looks like a decision.

## Repo settings

Settings change without a commit, so check them in every mode. Read them with GET calls:
```bash
gh api repos/{owner}/{repo} --jq '{default_branch, security_and_analysis, delete_branch_on_merge}'
gh api repos/{owner}/{repo}/rules/branches/<default> 2>/dev/null
gh api repos/{owner}/{repo}/branches/<default>/protection 2>/dev/null
gh api repos/{owner}/{repo}/environments --jq '.environments[] | {name, protection_rules}'
```
- **The default branch is protected**: no direct pushes, no force pushes, at least one review,
  and stale approvals dismissed. If deploys or applies run on push to it, this protection is the
  only gate on production.
- **CODEOWNERS** covers `.github/`, IaC, agent settings and auth code, so changes there need an
  owner's review.
- **Production environments** have required reviewers, and deploy credentials are bound to them.

Some of this needs admin rights or a paid GitHub plan on private repos. A 403 or 404 means
"not checkable", not a gap: record it under Not checkable and move on.
