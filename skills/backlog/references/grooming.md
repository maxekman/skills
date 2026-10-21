# `groom` and `triage` — the defect pass

Read a slice of the backlog, find what is malformed, propose every fix at once, apply on one
confirmation, verify each write. The batch is the unit of review: a groom that asks eight
times is a groom nobody runs twice.

## Step 1 — Scope

A groom needs a scope argument — a project or a team on Linear, a milestone or a label on
GitHub. Refuse a whole-backlog groom: the proposal gets too long to actually read, and an
unread proposal that gets a `y` is worse than no groom at all. If the user gives no scope, list
the projects (or milestones and label families) and ask.

Read once, with the fields the checks need. On GitHub that is the single `gh issue list` in
`github.md`, narrowed with `--search`, plus the not-planned closed set for check 3. On Linear:

```
list_issues(project: "<name>", limit: 100, fields: [
  "id", "title", "status", "statusType", "priority", "projectMilestone",
  "assignee", "labels", "parentId", "createdAt", "updatedAt", "url"
])
```

On Linear, relations (`blockedBy`, `blocks`, sub-issues) are not in that enum — they come from
`get_issue(id, includeRelations: true)`. Only fetch them for issues a relation check actually
implicates, not the whole slice.

If the slice hits the limit, say so and groom the first page rather than silently truncating.

## Step 2 — Checks

Each check has a detection rule and one proposed fix. Skip a check rather than guess when the
data to decide is missing — and skip it outright where the GitHub column says n/a.

| # | Defect | Detect (Linear) | GitHub | Propose |
|---|---|---|---|---|
| 1 | No priority | `priority == 0` and `statusType != triage` | Only with a priority-label scheme: no label from it | A tier, per the rubric, with a one-line reason |
| 2 | No home | `projectId` empty, `statusType` not `triage`/`canceled` | No label from a family most issues carry (e.g. `area:*`) | The project or label its title points at — or triage if genuinely unclear |
| 3 | Dead blocker | a `blockedBy` issue has `statusType` `completed` or `canceled` | Only a blocker closed *not planned* — judgment, not batched | Linear: `removeBlockedBy` that edge. GitHub: re-plan or remove, ask per issue |
| 4 | Assigned but parked | has `assignee`, `statusType == backlog` | n/a — assigned *is* started | Either `unstarted` or drop the assignee — ask which, per issue |
| 5 | Started, unowned | `statusType == started`, no `assignee` | n/a | Assign, or move back to `unstarted` |
| 6 | Stale | `statusType` `backlog`/`unstarted`, `updatedAt` older than 90 days | Unassigned, `updatedAt` older than 90 days | Close as stale — **always asks, never batched** |
| 7 | Orphaned child | `parentId` set, parent `statusType` `completed`/`canceled`, child open | `parent.state == CLOSED`, child open | Re-parent, or clear the parent and give it a home |
| 8 | Probable duplicate | two open issues, near-identical titles, same project | Same, same milestone or label family | Flag the pair for a human. **Never auto-close** |
| 9 | Urgent inflation | more than ~5 issues at `priority 1` in one project | Only with a priority-label scheme | No write — report it. The tier has stopped meaning anything |
| 10 | Milestone inversion | open blocker sits in a later milestone than the issue it blocks, or in none | Same, from `blocking` nodes | Move the blocker into the earlier milestone |

On GitHub, closed blockers are history, not defects: the rank and `is:blocked` already ignore
them, and removing them would bury a real proposal under edge deletions. Check 10 needs
relations, so on Linear fetch them only for issues in the slice that have blockers — the same
lazy rule as check 3.

Checks 6, 8, 9 and GitHub's 3 are judgment, not defects. Report them in their own section,
below the mechanical ones, and never fold them into the batch confirmation.

## Step 3 — Propose

Group by defect class, not by issue — the class is what the user is deciding about, and one
`y` should settle a whole class.

```
## Groom — <project>, 34 issues read

### Mechanical (apply as a batch)

no priority (4)
  INN-402  Rewrite aws/README.md against the Terraform      → 3 Medium   (no date pressure, agreed work)
  INN-403  Scope or drop the unscoped SNS grant             → 2 High     (in the current milestone)
  ...

dead blocker (2)
  INN-441  blockedBy INN-388 — INN-388 is Done              → remove edge
  ...

started, unowned (1)
  INN-417  Add E2E error-path coverage                      → assign to max, or back to Todo?

### Judgment (each asks separately)

stale >90d (1)
  INN-207  Spike: evaluate Temporal    last touched 2026-04-02   → close?

probable duplicate (1 pair)
  INN-388 / INN-455   "Sentry: add @sentry/react…" / "Wire Sentry into the frontend"

### Health

priority 1 Urgent: 7 issues — above the useful threshold, the tier is not discriminating.

Apply the 7 mechanical changes? [y/N]
```

State counts everywhere. "4 issues have no priority" is reviewable; a bare list is not.

## Step 4 — Apply

On confirmation, per issue:

- **One write per issue** — `save_issue` or `gh issue edit` — carrying only the fields this
  groom is changing. On Linear, never attach a `patch` to a call that also moves `state` — see
  contract rule 2 in `linear.md`.
- **Read the result back** and compare each changed field to what was asked: the
  `save_issue` response on Linear, a `gh issue view --json` on GitHub. An unconfirmed write is
  a failed write.
- A failure **does not abort the batch.** Keep going, collect the failures, and report them
  together — a stale patch on one issue is no reason to leave the other six unfixed.

Then report, with the failures impossible to miss:

```
✓ 6 applied
✗ 1 did not stick
    INN-441  removeBlockedBy INN-388
             → "Error: Failed to remove 1 relation(s)"
             relation still present on re-read. Needs the Linear UI.
```

If everything applied, say so in one line. Do not pad a clean run into a report.

## `triage`

The same loop, narrowed: on Linear, issues with `statusType: triage`, plus anything missing
both priority and project; on GitHub, issues carrying the repo's triage label if it has one,
otherwise open issues with no labels. Per issue propose a priority tier (GitHub: only with a
label scheme), a project or labels, and a milestone if the backlog uses them — that is a
*placement*, so the reasoning in `place` applies. An issue that cannot be placed stays in
triage with a note saying what is missing; parking it is a real outcome, not a failure.
