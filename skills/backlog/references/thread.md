# Thread — the anchor, who belongs to it, and when it stalls

`next` ranks from the work you are on, not from the backlog's global order. The **anchor** is the
issue set that work continues from; the **thread** is the open issues related to it. Both
sections of the output use the rank contract unchanged — the thread only decides which issues
are asked first.

## Finding the anchor

Take the first source that yields one, and print it as the output's first line:
`Anchor: #29 → #19 (Part of), parent #13`.

1. **Args.** Any issue or PR ref — `#29`, `owner/repo#29`, a URL, `ACME-407`. On GitHub a `#N`
   may be either; `gh pr view` fails on an issue, so try it first and fall back to
   `gh issue view`. A PR resolves to its issues:
   `gh pr view <n> --json closingIssuesReferences,body,headRefName`. `closingIssuesReferences`
   holds only the closing keywords (`Closes`, `Fixes`), so also scan the body for `Part of #N`
   and `Refs #N` — the issue a PR only advances is usually the one the thread continues. On
   Linear, the ID sits in the PR title (`ACME-407 / Title`) or the branch name.
2. **The conversation.** Issues and PRs this session implemented, wrapped up, verified or filed.
   The most recent wins; several from the same piece of work are one anchor set.
3. **The workspace.** A fresh session has no conversation, but the workspace remembers:
   - `jj log -r '@ | @-' --no-graph -T 'bookmarks ++ "\n"'` — a bookmark carrying an issue ID or
     slug, as `/task implement` pins them.
   - After `/wrapup`, `@` sits on trunk with no bookmark. Read the refs from your recent trunk
     commits instead, taking the newest commit that has any:
     `jj log -r 'ancestors(trunk(), 15) & mine()' --no-graph -T 'description ++ "\n"'`.
   - A non-default workspace name (`jj workspace list`) often names the thread. Use it as a
     scope hint that maps onto an existing label or milestone, never as an anchor on its own.
4. **Your in-flight issues.** Several → anchor on the most recently updated and leave the rest
   on the in-flight line.

Nothing found → rank globally and say "no thread found — global ranking". Don't guess an anchor
from titles: a wrong thread is worse than none, because the reason lines then argue for it.

A closed anchor is normal — the merge just closed it. Its relations still define the thread, but
the open-issue read doesn't return it, so fetch it once: GitHub
`gh issue view <n> --json parent,blocking,blockedBy,milestone,labels`, Linear
`get_issue(id, includeRelations: true)`.

## Who is in the thread

Closest tier first. Within a tier, order by the rank contract; the candidate filter is the same
as the global one (open leaf, nobody on it).

**(a) Direct relations.**
- What the anchor blocks — the issues its merge just moved closer to free.
- Siblings — open sub-issues of the anchor's parent. If the parent is closed, walk up to the
  nearest open ancestor. GitHub: rows of the one graph read with the same `parent.number`;
  Linear: `list_issues(parentId: …)`.
- Blockers — open `blockedBy` of the anchor and of its siblings, cross-repo nodes included.
  Name a cross-repo node by its URL and state; don't fetch it.

**(b) Session follow-ups.** Issues this session filed or named as leftovers — `/wrapup`'s
follow-ups, a PR body's "follow-up in #N".

**(c) Same milestone or area label.** Only to fill slots that (a) and (b) leave, up to `n`. Area
labels only (`area:ui`, `docs`): type labels like `bug` or `enhancement` span the whole backlog
and would rebuild the global ranking under another name.

The reason line names the tie: `sibling of #19 under #13 (7/10 done)`, `unblocked by #29`,
`filed in this session`, `same milestone as #19`.

## A stalled thread

The thread is stalled when (a) and (b) hold no unblocked candidate. Say so first, naming the
blocker that holds up the most members, then the move that frees it:

| Blocker | Move |
|---|---|
| Yours, in flight | Finish it — name what it still waits on |
| Someone else's | Name the owner; the move is a nudge, not a pick |
| In another repo | `Continue there: /skills:backlog next owner/repo#N`, run from that repo |

A member that is doable now except for one acceptance line that waits on the blocker stays
listed under it, with the catch spelled out. Then `Elsewhere` as usual — a stalled thread is
exactly when the global pick matters most.

## Shape

```
Anchor: #29 → #19 (Part of), parent #13 Launch the website
In flight (yours): #19 Prepare the repo to go public — waits only on the PR #4 reword

Continue this thread
  Waits on acme/app#258 (open, other repo): it blocks #21 and holds #20's video ID.
  Continue there: /skills:backlog next acme/app#258, run from acme/app
  1. #20 Add a click-to-load demo video — sibling of #19 under #13 (7/10 done). Buildable now
     with no video ID; the network-panel check waits for #258, so it stays open after its PR.

Elsewhere
  1. #42 Fix broken links in the footer — earliest milestone (M2), unblocks 2
  Nothing here outranks the thread on priority or milestone.

Blocked
  #21 Publish the site on launch day — blocked by acme/app#258, #19
```
