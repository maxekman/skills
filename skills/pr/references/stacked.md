# Stacked PRs

A PR is "stacked" when its base is another in-flight PR (a feature bookmark between trunk and `@-`), not `main`/`master`.

## Detect a stacked PR

After bookmark management, check for a parent bookmark between trunk and `@-`:

```bash
jj log -r '(trunk()..@-) & bookmarks()' --no-graph -T 'bookmarks ++ "\n"'
```

If a bookmark is found, check whether it has an open PR:

```bash
gh pr list --author @me --head <parent-bookmark> --json number,title,url
```

Match → record `PARENT_BOOKMARK` and `PARENT_PR_NUMBER`. No match → not stacked, proceed normally.

## Create a stacked PR

Pass the parent bookmark as `--base`:

```bash
gh pr create --head <branch-name> --base <parent-bookmark> --title "..." --body "..."
```

Prepend a stack notice to the description body (before any template content):

```
> **Stack**: based on #<parent-pr-number> — review/merge that first.
```

## Update a stacked PR

Push updates the PR normally if the parent is still open. If the parent merged, suggest the user run `/pr rebase` to rebase onto main and retarget.

```bash
gh pr view <parent-pr-number> --json state
```

## Rebase a stacked PR (`/pr rebase`)

Triggered when the parent merged and the child needs to retarget `main`:

1. Identify the current PR's bookmark and number.
2. `jj git fetch`
3. `jj rebase -d main`
4. `jj tug` — verify with `jj log -r 'closest_bookmark(@-)'` first.
5. `jj git push --bookmark <branch-name>`
6. Retarget the PR base on GitHub:
   ```bash
   gh pr edit <pr-number> --base main
   ```
7. Report the updated PR.

If rebase has conflicts, STOP and ask the user to resolve manually.
