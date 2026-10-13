# Sync edge cases

The happy path in `SKILL.md` covers an empty `@` sitting on the merged stack. This file covers
the three ways that goes differently.

## Merged commits survived the move

Fetch usually abandons the merged commits on its own and rebases `@` onto trunk. When it
doesn't, they linger as a side head in `jj log` that looks like unfinished work.

Abandon exactly the commits the PR carried, using the same revset that found them:

```bash
jj abandon '::visible_heads() & (commit_id(<oid1>) | commit_id(<oid2>))'
```

If the PR's bookmark is still listed locally, forget it rather than delete it:

```bash
jj bookmark forget <headRefName>
```

`delete` records a deletion to push, which would reach for a remote branch GitHub has usually
already removed; `forget` is local-only. Report what was abandoned by short id and title. It is
reversible with `jj undo`, and saying so is part of the report.

## The move was refused

Name the blockers by title so the user recognizes them, then work out which case it is.

**A stacked child PR.** The commits above the merged ones carry a bookmark with an open PR:

```bash
jj log -r '(trunk()..@-) & bookmarks()' --no-graph -T 'bookmarks ++ "\n"'
gh pr list --head <bookmark> --state open --json number,title,baseRefName
```

An open PR there means the parent merged and the child now carries stale copies of the parent's
commits. That is `/skills:pr rebase`'s job — it rebases, moves the bookmark, pushes, and
retargets the base. Suggest it; don't do that work here.

A child can also sit beside `@` rather than under it. Check descendants of the merged commits
that `@` doesn't contain:

```bash
jj log -r '(commit_id(<oid1>) | commit_id(<oid2>)):: & bookmarks() ~ ::@'
```

**Unrelated work.** Commits in `trunk()..@-` that belong to no PR. Leave them; the user may be
mid-thought. Mention that `jj lift` would rebase the whole stack onto the new trunk, but don't
run it — rebasing someone's in-progress work is their decision.

**Working-copy changes.** `@` is non-empty. Say so and stop the sync; the rest of the wrap-up
(live systems, leftovers) still runs, since neither depends on where `@` sits.

## Secondary workspaces

`Repo info` showing `origin <url>` means a secondary jj workspace with no `.git`, so unqualified
`gh` calls fail. Extract `owner/repo` from the URL and pass `-R owner/repo` to every `gh pr` and
`gh run` call; `gh api graphql` already takes owner and repo as query variables. The pr skill's
`references/workspaces.md` has the full treatment.

Other workspaces of the same repo are other sessions' working copies. Never touch their `@` —
`jj new trunk()` only ever moves this workspace's.
