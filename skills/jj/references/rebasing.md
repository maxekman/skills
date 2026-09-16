# Rebasing, squashing, and stack management

## Rebase for linear history

Moving commits with `-d` can create branching/parallel history. Use `-B` (before) and `-A` (after) to insert in linear sequence:

```bash
jj rebase -r commit-to-move -B parent-commit -A child-commit
```

`jj lift` (alias) handles the common case: rebase the entire feature stack onto trunk after `jj git fetch`.

## Squash safety: only mutable history

`jj squash` rewrites commits. **Only commits in `trunk()..@` are mutable.** Commits on `trunk()` are published history — rewriting them breaks collaborators.

Before any `--from`/`--into`:

```bash
jj log -r 'trunk()..@'  # only these are valid squash targets
```

Anti-patterns:

- `jj squash --into <rev-on-main>` — rewrites published history.
- `jj squash --from <rev> --into @-` when `@-` is on trunk — same problem, less obvious.
- Squashing a `wip:` commit that has been pushed/landed.

If a fix belongs in a landed commit, don't rewrite it. Make a follow-up:

```bash
jj commit -m "fix(scope): correct oversight from <hash>"
```

## Squash basics

- `jj squash` — move working copy into parent (most common).
- `jj squash --from <rev> --into <rev>` — move between specific commits.
- `jj squash -m "message"` — move into parent with a new message (overrides parent's).
- Verify with `jj diff --stat -r @-`.

## Absorb: auto-route fixups into a stack

When you have a stack (`trunk()..@`) and the working copy contains fixups for several earlier commits, `jj absorb` distributes each hunk to the commit that last modified those lines.

```bash
jj absorb              # route all working-copy hunks
jj absorb <paths>      # limit to specific files
```

After absorb, **always review**: `jj op show -p`. Absorb moves hunks silently and mistakes are easy to miss.

When to use which:

- **absorb** — fixups span multiple commits in your stack (e.g., formatter ran across files touched by different commits).
- **split** — working copy has unrelated changes that belong in *new* commits.
- **squash** — all working-copy changes belong in one specific existing commit.

Ambiguous hunks (multiple ancestors touched the same lines) stay in the source revision — handle manually with `jj squash --into <rev> <paths>`.

## Split behavior

`jj split -m "msg" <files>` creates a new commit from the specified files; the rest stays in `@`.

- **Describe before splitting**: `jj describe -m "msg"` first so the new (parent) commit inherits the message; then `jj describe` the remainder.
- **Deleted files** match by original path. If split warns "No matching entries", the file may already be in the right half.
- **Use case**: keep WIP on top by splitting out the finished work — it becomes the parent of `@`.

For paths with colons or parens, see `edge-cases.md` (fileset quoting).
