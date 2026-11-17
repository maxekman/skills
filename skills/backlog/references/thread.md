# Thread — the anchor, who belongs to it, and when it stalls

`next` ranks from the work you are on, not from the backlog's global order. The **anchor** is the
issue set that work continues from; the **thread** is the open issues related to it. Both
sections of the output use the rank contract unchanged — the thread only decides which issues
are asked first.

## Finding the anchor

Take the first source that yields one, and print it as the output's first line:
`Anchor: PR #29 / Add the launch checklist → #19 / Prepare the repo to go public (Part of),
parent #13 / Launch the website`.

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
- Related (Linear) — issues linked to the anchor as related, from the same
  `get_issue(includeRelations: true)` read. Someone drew that link by hand, so it is as
  deliberate as a blocking edge. GitHub has no such edge.

**(b) Session follow-ups.** Issues this session filed or named as leftovers — `/wrapup`'s
follow-ups, a PR body's "follow-up in #N".

**(c) Same project, then area label.** Only to fill slots that (a) and (b) leave, up to `n`.
- Linear: the anchor's project, `list_issues(project: …)`, with issues in the anchor's own
  project milestone first. A project is the tracker's container for one topic, and a milestone
  inside it is a phase of that topic.
- Then area labels only (`area:ui`, `docs`): type labels like `bug` or `enhancement` span the
  whole backlog and would rebuild the global ranking under another name.
- Not milestone, on either backend. GitHub milestones are usually release-wide (`M1`), so they
  rank but don't mark a topic.

The reason line names the tie: `sibling of #19 under #13 (7/10 done)`, `unblocked by #29`,
`related to ACME-407`, `filed in this session`, `same project as ACME-407`.

**Overflow.** Whatever the thread holds beyond `n` goes on one line under the section, from the
reads already made and with no relation fetch: `Also in this thread: INN-1190 / Show the journey
map (sibling) · 6 more open in project "Journey v0"`. GitHub counts the anchor's area label
instead. It shows the topic has more without spending a slot on a looser tie, and `next 6`
opens it up.

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
exactly when the global pick matters most, and the only time the closing pick comes from it.

## Elsewhere

One flat read, ranked on the rank contract, with the thread's members left out:

- **Linear** — `list_issues` over the anchor's team, `statusType` `backlog` or `unstarted`, with
  `project` added to the ranking `fields` so the anchor's project can be left out, then
  relations for contenders only, as in `references/linear.md` *Relations for the rank*: their
  `blocks` edges are followed through issues already in that slice, never out of it.
- **GitHub** — the rows of the one graph read the thread came from, minus the thread.

"The thread" here includes the overflow line. On Linear that is the anchor's whole project, so
Elsewhere means another topic rather than the project's next few issues. When excluding it
leaves little, show what remains and say `most open work is in project "Journey v0"`.

Don't widen it by following the anchor's parent, what the anchor blocks, or what those block.
Every issue found that way feeds something the thread also feeds, so it outranks the thread by
construction, and the section becomes a list of blockers arguing against the work you are on.

The outrank line fires only when an Elsewhere issue is strictly higher than every thread pick on
priority tier, or sits in an earlier milestone: `INN-704 is Urgent, above everything in this
thread.` Equal tiers, or no milestones, give no line. It informs and never moves the pick — you
can overrule a one-line note at a glance, while a pick that hedges between two threads leaves
you to redo the ranking yourself.

## Side lines

- **In flight (yours)** — name the ones in the thread (the anchor's parent or project, or a
  direct relation). Collapse the rest into one line:
  `+2 more in flight elsewhere (INN-704 / Rotate the API keys, INN-1103 / Drop the v1 export)`.
  Finishing a thread member is often the real next step, so it leads; the rest is context.
- **Blocked** — thread members that are blocked, plus an Elsewhere issue only if it would
  otherwise have made Elsewhere's top `n`. Name each blocker with its owner and state from the
  read you already have. Don't fetch the blocker's blockers: one hop says what to nudge, and
  the second hop is how a ranking drifts off topic.

## Shape

```
Anchor: PR #29 / Add the launch checklist → #19 / Prepare the repo to go public (Part of),
  parent #13 / Launch the website
In flight (yours): #19 — waits only on PR #4 / Reword the launch post
  +1 more in flight elsewhere (#37 / Record the demo video)

Continue this thread
  Waits on app#258 / Expose the video ID (open, other repo): it blocks #21 and holds #20's
  video ID.
  Continue there: /skills:backlog next acme/app#258, run from acme/app
  1. #20 Add a click-to-load demo video — sibling of #19 under #13 (7/10 done). Buildable now
     with no video ID; the network-panel check waits for app#258, so it stays open after its PR.
  Also in this thread: 3 more open with label area:web

Elsewhere
  1. #42 Fix broken links in the footer — earliest milestone (M2), unblocks 2

Blocked
  #21 Publish the site on launch day — blocked by app#258, #19

Pick: #20, then /task implement #20
```
