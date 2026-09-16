# Git integration and PR workflow

## Submodules

jj does NOT support git submodules. When `git submodule status` shows changes, commit them with git after the jj working copy is clean:

```bash
git add <submodule-path>
git commit -m "chore: update submodule to <commit-hash>"
```

## Feature bookmarks

Never move protected bookmarks (`main`, `master`, `develop`, `staging`, `prod`). Create feature bookmarks for PR work:

```bash
jj bookmark create feature/my-feature -r @
# or use the bc alias to target the latest non-empty ancestor:
jj bc feature/my-feature

jj bookmark list  # check positions
```

## Pushing

```bash
# Always dry-run first
jj git push --dry-run

# Push a specific feature bookmark
jj git push --bookmark feature/my-feature

# Push to a non-default remote
jj git push --remote <fork> --bookmark feature/my-feature
```

Only push feature bookmarks. Never push `main`/`master` unless explicitly asked.

## Push safety

Before any `jj git push`:

1. Run `jj git push --dry-run` to see exactly what would push.
2. If the bookmark is protected (`main`, `master`, `develop`, `staging`, `prod`), STOP.
3. If you used `jj tug`, it may have moved a protected bookmark. Run `jj undo` immediately and verify with `jj bookmark list`.

Safe pattern after committing: `jj bc <feature-name>` → `jj git push --bookmark <feature-name>`. Never combine `jj tug` with push.

## Merged PR detection

Pushing to a merged PR's branch is a silent no-op on GitHub — the changes go nowhere. Before pushing an existing bookmark:

```bash
gh pr list --head <bookmark-name> --state merged --json number,url --jq '.[0].number'
```

If a merged PR exists, **STOP**. The branch is closed; pushing accomplishes nothing. Tell the user and suggest `/pr` for a new PR.

**Strongest signal**: if `closest_bookmark(@-)` resolves to `main`, the parent is already on trunk. Any feature bookmark you're about to reuse almost certainly had its PR merged. Verify before reusing the old name.

## Creating pull requests

Push the bookmark first (`jj git push --bookmark <name>`), then use the `/pr` skill for the full PR workflow.
