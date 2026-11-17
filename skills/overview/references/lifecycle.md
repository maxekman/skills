# Workspace lifecycle, offers and pushes

## Which issue a workspace is on

First that names one:

1. **Override** in `notes.json`. The user said so.
2. **`stack_ids`**: a tracker ID in a `trunk()..@` commit or a bookmark. `/skills:pr` builds
   bookmarks like `max/dev-35-…`, and the snapshot already turns those into `DEV-35`.
3. **`todo_ids`**: a `## ACME-407 — …` header that `/task implement` wrote into `TODO.md`.
4. **`prompt_ids`**: the IDs in the latest prompt that named any, e.g.
   `/skills:task implement #57`. This is the earliest signal and the weakest: it is a guess until
   a commit or bookmark confirms it.

When several IDs tie at one level, show them all and ask once. A busy workspace that no source
names is `?` on the board.

## States

| State | From the snapshot | Do |
|---|---|---|
| **free** | `free: true`, no open PR for its bookmarks | When its session is idle and not `asked`, or it has none, show a next-up suggestion (below) |
| **your turn** | free, but a session is `asked`: idle, and its last message ends on a question | Nothing. The user owes that session an answer, so it is not free |
| **working #N** | not free, or a session's prompt names an issue | Record it. Watch for `waiting_long` and `stalled` |
| **parked** | not free, no session, no PR | Nothing. Work left in the workspace; the board shows its commits. Ask what it is only if the user brings it up |
| **in review #N** | a bookmark has an `OPEN` PR | Report checks and review. Push on `fail` or `CHANGES_REQUESTED` |
| **merged #N** | its PR is `MERGED` | The merge sequence below |

"In review" is not free. The PR's context still lives in that session, and follow-up work has
to wait for the merge anyway, because PRs never stack.

A workspace with no live session is still on the board: its stack tells what was left there.

## The merge sequence

When a PR moves to `MERGED`:

1. **Did the issue close?** GitHub: is `#N` in the PR's `closes`, and is its state `CLOSED`
   in `issues`? Linear: fetch the issue and check that its `statusType` is `completed`. If it is
   still open, offer to close it with a one-line comment, "Closed by PR #M". GitHub:
   `gh issue close N -R owner/repo --reason completed --comment "…"`. Linear: set its state
   through `save_issue`, following `/backlog`'s Linear write contract.
2. **What comes next?** In a Linear repo, refresh the team's graph first (`references/graph.md`).
   Say the merge in one chat line that names what it unblocked: the issues it blocked that now
   have no open blocker left, e.g. "PR #88 merged · unblocks DEV-44, DEV-45". Linear: compare
   the graph before and after the refresh. GitHub: `gh issue view N -R owner/repo --json blocking`
   gives them, with each one's other blockers in `gh issue view M --json blockedBy`.
   Then invoke `/skills:backlog next` for that repo only, asking for one more
   item than there are free workspaces. The guide's cwd is not the repo, so name the repo
   (`-R owner/repo` for `gh`, or the Linear team). Neither tracker can store an order, so the
   way to "promote" depends on the tracker:
   - **Linear**: offer to move the top items from Backlog to Todo, an `unstarted` state, up to
     that cap.
   - **GitHub**: there is no "up next" state, and assigning an issue would mark it in flight.
     Show the ranked items as `next` hints in `notes.json`. Write nothing to the tracker.

   Set the merging workspace's `next` now, before it is free: `/skills:wrapup` in that
   workspace reads it from `notes.json` and ends its report with it, so the user can `/clear`
   and start the next item there.
3. **Wrapup belongs to the worker.** It moves that workspace's `@` onto trunk, which only the
   session that owns it may do. The snapshot sets `wrapup_ready` only when that session still
   owns the merge: the stack holds nothing but the merged PR, the workspace has exactly one
   live session, it is idle, and its latest prompt that named an issue named this PR's issue
   or `#M` (or none ever did). A session that moved on to other work in the same workspace
   fails it, so the message would only make it decline.
   - With `"auto_wrapup": true` in the config, send `/skills:wrapup #M` to that session with
     `SendMessage` when `wrapup_ready` turns true. Send once per PR: check `state.md` first, and
     log the send there. Then say one line in chat, e.g. "sent wrapup to opendecks-3 for PR
     #70".
   - Otherwise, or when the PR merged but `wrapup_ready` stays false, set the workspace's
     `note` to "needs wrapup" in `notes.json`.

   Judge the outcome from the snapshot, never from what the session said. **Done** once the
   workspace's `pr` is no longer `#M`, because wrapup moved it off the merged stack: log
   "wrapped up" and clear the note. **Declined** when the session went busy and back to idle
   after the send with `pr` still `#M`: log it, set the note, and never send for that PR again.
   Anything else is still in progress; the note on the board is enough, so no timeout.

Batch the offers from one merge into a single question, and carry each one out on its own yes.

## Suggesting the next item

The user picks up work themselves, often before the guide has said anything. A suggestion is a
hint on the board, not a plan that the user then departs from. For a free workspace whose
session is idle, or that has no session, take the top ranked item not already shown for
another workspace. Set it as that workspace's `next` in `notes.json`, with the reason in one
short clause: `"#63 (P1, unblocks #64 and #66)"`. The board shows it while the workspace is
free and hides it once work starts, so a suggestion the user passes over needs no cleanup and
no comment. Mention a suggestion in chat at most once, when the workspace first goes free. If the user asks to hand it to the session, send `/skills:task implement #63` with
`SendMessage` to the session `name` from the snapshot. Never send to a `busy` session, because
the message would land in the middle of its turn.

## Pushes

Send a `PushNotification` only when the user is needed:

- `waiting_long` turned true: a session has waited more than 5 minutes for permission or
  input. Name the session and its `waiting_for` when there is one.
- A PR's checks turned `fail`, its review turned `CHANGES_REQUESTED`, or it turned
  `conflicts`: usually another merge changed the same lines on trunk, so name that merge.
  These go to the user, not the session. Each needs a judgement (a flaky run, a review to push
  back on, which side of a conflict wins), and `/skills:pr` stops on rebase conflicts for the
  user to resolve.
- A workflow on the default branch turned `fail` (`trunk`), or a lane turned `fail` or
  `behind` (`lanes`). Name the workflow and the merge that went in just before it, which is
  usually the cause. When the lane's `cut` is not empty, say those merges are not live either:
  their own deploys were cancelled in favour of this one. For `behind`, say the target is
  behind the branch at that commit and nothing is queued to catch it up. A workflow or lane
  that was already red when the guide started goes on the board, not into a push.
- `stalled` turned true: a busy session has gone 20 minutes without writing to its transcript.
  It is probably hung.

Everything else goes on the board only, or into one short chat line: merges, a session starting
work, commits, a PR opened, checks turning green, a deploy starting or passing, suggestions, and
the guide's own writes.
