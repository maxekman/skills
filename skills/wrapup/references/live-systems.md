# Live systems

The question is narrow: did the merge reach the environments it auto-deploys to, and are they
up? Not a full verification of the feature, not a prod check, and never a deploy of your own.

## 1. A repo-local verify skill wins

If the repo ships its own skill for this — `.claude/skills/verify-deploy/` or anything named
for verifying or checking a deploy — invoke it and use its result for this section. It knows the
repo's environments, auth, and failure modes better than generic discovery will, and running both
duplicates the slowest part of the wrap-up. Report what it found and skip the rest of this file.

## 2. Classify the environments

Read the deploy workflows in `.github/workflows/`. Each `environment:` block names an
environment (`url:` often sits beside it); the workflow's `on:` block says how it gets there:

| Trigger | Means |
|---|---|
| `push` to the default branch | auto-deployed by this merge — check it |
| `workflow_run` on a workflow that runs on push | auto-deployed, one hop later — check it |
| `workflow_dispatch`, or `push` on `tags: v*` | needs a manual promotion — report it, don't check it |
| a protected environment with required reviewers | a human gate, usually prod — report it, don't check it |

A repo can mix these: dev on push, staging on a tag, prod behind reviewers. Only the first two
rows are this merge's responsibility. Reporting the others as "not auto-deployed — needs <what>"
tells the user what promotion is still theirs to do.

`CLAUDE.md`/`AGENTS.md` often name the environments and their URLs more plainly than the
workflows do, and they are where health endpoints and read-only inspection rules live. Read
their deploy or operations sections before probing anything.

## 3. Wait for the runs

`workflow_run` children carry the same head SHA as the push that started the chain, so the
`gh run list --commit` query from the skill's step 3 catches build, deploy, and smoke together.

A chain starts one workflow at a time, so a deploy may not exist yet while the build is still
running. Watch whatever is in progress, then run that query again to pick up what it started:

```bash
gh run watch <databaseId> --exit-status --interval 30
```

Budget about 20 minutes in total. Past that, report the runs still going with their URLs rather
than blocking the wrap-up on a slow pipeline.

A failed run is the headline of the report. Pull the cause, not the whole log:

```bash
gh run view <databaseId> --log-failed | tail -30
```

## 4. Probe, lightly

One read-only check per auto-deployed environment, taken from the repo's own docs:

- A documented health URL → `curl -fsS -o /dev/null -w '%{http_code} %{time_total}s\n' <url>`.
- A documented read-only status task (`mise run deploy-status`, `make smoke-*`, a
  `scripts/healthcheck`) → run that instead; it encodes checks a bare `curl` can't. These fall
  outside the skill's pre-approved tools, so expect a permission prompt.

Smoke workflows that already ran green in step 3 count as the probe — don't repeat them.

No documented endpoint and no smoke run → say the deploy run succeeded but nothing confirmed the
service is answering. Don't guess at URLs.

## Report shape

```
Live systems
  dev      deploy-dev.yml ✓ 3m12s · smoke-dev.yml ✓ · GET /health → 200
  staging  not auto-deployed — needs a release tag + dispatch
  prod     manual gate, not checked
```

## Read-only, always

Everything here observes. These are out of bounds even when the docs show how:

- Dispatching or re-running a workflow (`gh workflow run`, `gh run rerun`).
- Anything that writes to an environment's data — resets, seeds, migrations, read-write DB
  sessions.
- Mutating cluster state (`kubectl apply|delete|scale|rollout restart`, `helm upgrade`), and
  switching contexts — pass `--context` per command instead, as repos that document live
  inspection tend to require.
- Fetching or printing secrets to authenticate a probe. If a probe needs a token the docs
  obtain through a task (`mise run staging-token`), using that task is fine; echoing the token
  is not.

If the right next step is one of these — a failed deploy that needs a re-run — say so and leave
the command for the user.
