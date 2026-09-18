---
name: pr
argument-hint: "[branch name or title]"
allowed-tools: Bash(gh *), Bash(jj *), Read, Grep, Glob
description: GitHub PR creation and updating with jj bookmark integration - handles branch creation, push, PR workflow, updating existing PRs, creating PRs from GitHub issues (#N), and stacked PRs (auto-detects parent bookmarks, sets --base, supports rebase after parent merge)
---

# GitHub PR Creation & Update

Create or update pull requests using jj bookmarks and GitHub CLI. Keep PR descriptions terse — bullets ≤15 words, no paragraphs, no background context. Fill templates with "what changed", not "why/how".

## Context

- `jj status`: !`jj status`
- Bookmarks: !`jj bookmark list`
- Recent commits: !`jj log --limit 5`
- Repo info: !`gh repo view --json name,owner,defaultBranchRef 2>/dev/null || jj git remote list 2>/dev/null || echo "no remote detected"`

## Task

Create or update a PR for current changes: $ARGUMENTS

If no arguments, decide new-vs-update from bookmarks and `gh pr list --author @me`. Then look for a tracker ID — most commits in this user's workflow come from `/task implement <id>` and the issue link must survive into the PR for Linear/GitHub to auto-attach it. See step 3 for how the tracker ID drives the bookmark name.

With arguments, parse for: branch name, title, base override, draft flag, or `rebase` (rebase a stacked PR after its parent merged).

## Workflow

The happy path is short — five steps. Skip the references unless their signal fires.

### 1. Validate

Working copy must be empty. If `jj status` shows changes, STOP — commits go through `/jj` first. Verify `@-` has content with `jj show @-`.

### 2. Detect existing PR

```bash
gh pr list --author @me --json number,headRefName,title,url
```

Match bookmark names against open PRs to decide **new** or **update**.

If a bookmark exists but has no open PR, check for a merged one before reusing:

```bash
gh pr list --head <bookmark-name> --state merged --json number,title,url --jq '.[0]'
```

Merged → treat as **new PR**, prefer a fresh bookmark name. Reusing a merged bookmark silently pushes to a closed PR.

### 3. Bookmark

**Pick the name first.** For NEW bookmarks, use the first option that fires — earlier options preserve the canonical Linear slug, which is what the tracker matches against:

1. **Linear branch name already in this session's context.** If `/task implement <id-or-url>` ran earlier, its Delivery plan pinned a `**Branch**:` line (e.g. `max/dev-35-set-custom-domains-in-staging`), taken from the issue's `gitBranchName` or its URL slug. Use that string verbatim — it's what Linear expects and it round-trips cleanly when the PR is reopened or rebased. `/task` may also pass it as the argument to this skill; an explicit argument wins.
2. **Tracker ID in a `**/TODO.md`.** Check section headers (`## ACME-407 — Add rate limiting`) first, then trailing item tags (`- [ ] … [ACME-407]`, `[#42]`). `/task implement` writes the header form when it seeds a breakdown, so this survives a session boundary that the context above does not. Build the name as in option 3.
3. **Tracker ID in `trunk()..@` commits, no `/task` context.** Scan `jj log -r 'trunk()..@' -T description` for `[A-Z]+-\d+`. Construct `<git-user>/<tracker-id-lowercase>-<kebab-from-commit-title>` to mirror Linear's format. Get `<git-user>` from the local part of `jj config get user.email` (e.g. `max@looplab.se` → `max`). Linear matches on the tracker ID regex, not the exact slug, so close-enough is fine.
4. **No tracker ID anywhere.** Use `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/` — match conventions from `gh pr list --limit 10`.

Then create or move:

```bash
jj bc <branch-name>   # NEW: bookmark on @- (latest non-empty ancestor)
jj tug                # UPDATE: move closest bookmark to @-
```

Targeting a commit other than `@-` needs the full form — `jj bc` is aliased with `-r` already baked in, so passing `-r` again errors with "cannot be used multiple times":

```bash
jj bookmark create <branch-name> --revision <change-id>
```

Before `jj tug`, run `jj log -r 'closest_bookmark(@-)'`. If it resolves to a protected bookmark (`main`, `master`, `develop`, `staging`, `prod`), do NOT tug — create a new feature bookmark with `jj bc <name>` instead.

### 4. Push

```bash
jj git push --bookmark <branch-name>
```

### 5. Create or update PR

```bash
# NEW
gh pr create --head <branch-name> --title "<title>" --body "<description>"
# Forked repo:
gh pr create --head <user>:<branch-name> --title "<title>" --body "<description>"

# UPDATE — push already updated the PR. Optionally comment:
gh pr comment <pr-number> --body "Updated with latest changes"
```

Return the PR URL.

## When to Read References

Don't read these by default — only when the signal in parentheses is present.

- `references/issue-and-pr-refs.md` — args contain `#N` (e.g. `/pr #26`). Disambiguates PR vs issue, seeds a new PR from an issue.
- `references/stacked.md` — args contain `rebase`, OR `jj log -r '(trunk()..@-) & bookmarks()'` shows a non-empty parent bookmark. Covers `--base` to parent and the rebase-after-parent-merge flow.
- `references/workspaces.md` — `Repo info` shows `origin <url>` (secondary jj workspace) instead of JSON. Covers slug extraction and `-R owner/repo` for every `gh` call.
- `references/templates.md` — when writing the PR description body. Covers project template paths and the fallback.

Most PRs trigger none of these. The 5-step workflow above is enough.

## Branch Naming

Step 3 above has the full priority order. Quick reference:

- Tracker-ID work → `<user>/<tracker-id-lower>-<slug>` (Linear's format).
- Anything else → `feat/`, `fix/`, `refactor/`, `docs/`, `test/`, `chore/` — pick from `gh pr list --limit 10`.

## PR Title Format

Default: `<type>(<scope>): <description>` — match conventions from existing PRs.

**When a tracker ID is in the branch name or args** (`EL-3141`, `DEV-169`, `PROJ-42`), use `<TRACKER-ID> / <description>` instead. The tracker ID *replaces* the conventional prefix — don't combine the two. Convert the slug to a human-readable title in sentence case.

Examples:
- No tracker ID → `feat(auth): add OAuth2 login support`
- `/pr max/el-3141-decommission-visma-integration` → `EL-3141 / Decommission visma integration`
- `/pr max/dev-169-tenant-configurable-background` → `DEV-169 / Tenant configurable background`

Don't write `feat(branding): tenant-configurable background (DEV-169)` — the tracker ID goes in the prefix slot, not in parens at the end.

## Tracker Links

Scan commit messages for tracker IDs (`ABC-123`, `#42`). Also check `**/TODO.md` for recently checked-off items (`- [x]`) with tracker IDs. Include them in the PR description — Linear IDs as `ABC-123`, GitHub issues as `Closes #42`.

## Safety

- **NEVER** create a PR if the working copy isn't empty — commit first via `/jj`.
- **NEVER** create or move bookmarks named `main`, `master`, `develop`, `staging`, `prod`.
- **NEVER** commit changes from this skill — commits belong to `/jj`.
- **NEVER** include secrets in PR descriptions or add AI attribution.
- Use feature-branch patterns (`feat/`, `fix/`, etc.) for bookmarks.
- Verify bookmark position before pushing.

## Errors

- **Working copy not empty**: STOP — `/jj` first.
- **Bookmark already exists**: `jj tug` to move it forward.
- **Push fails**: check `gh auth status` and remote permissions.
- **Multiple matching PRs**: use the most recent or ask the user.
- **Rebase conflicts**: STOP — user resolves manually, then retry.
- **Fork detection**: use `--head <username>:<branch>` syntax.
