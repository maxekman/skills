# `groom` and `triage` — the defect pass

Read a slice of the backlog, find what is malformed, propose every fix at once, apply on one
confirmation, verify each write. The batch is the unit of review: a groom that asks eight
times is a groom nobody runs twice.

## Step 1 — Scope

A groom needs a scope argument — a project or a team. Refuse a whole-workspace groom: the
proposal gets too long to actually read, and an unread proposal that gets a `y` is worse than
no groom at all. If the user gives no scope, list the projects and ask.

Read once, with the fields the checks need:

```
list_issues(project: "<name>", limit: 100, fields: [
  "id", "title", "status", "statusType", "priority", "projectMilestone",
  "assignee", "labels", "parentId", "createdAt", "updatedAt", "url"
])
```

Relations (`blockedBy`, `blocks`, sub-issues) are not in that enum — they come from
`get_issue(id, includeRelations: true)`. Only fetch them for issues a relation check actually
implicates, not the whole slice.

If the slice hits the limit, say so and groom the first page rather than silently truncating.

## Step 2 — Checks

Each check has a detection rule and one proposed fix. Skip a check rather than guess when the
data to decide is missing.

| # | Defect | Detect | Propose |
|---|---|---|---|
| 1 | No priority | `priority == 0` and `statusType != triage` | A tier, per the rubric, with a one-line reason |
| 2 | No project | `projectId` empty, `statusType` not `triage`/`canceled` | The project its labels and title point at — or triage if genuinely unclear |
| 3 | Dead blocker | a `blockedBy` issue has `statusType` `completed` or `canceled` | `removeBlockedBy` that edge |
| 4 | Assigned but parked | has `assignee`, `statusType == backlog` | Either `unstarted` or drop the assignee — ask which, per issue |
| 5 | Started, unowned | `statusType == started`, no `assignee` | Assign, or move back to `unstarted` |
| 6 | Stale | `statusType` `backlog`/`unstarted`, `updatedAt` older than 90 days | Close as stale — **always asks, never batched** |
| 7 | Orphaned child | `parentId` set, parent `statusType` `completed`/`canceled`, child open | Re-parent, or clear `parentId` and give it a project |
| 8 | Probable duplicate | two open issues, near-identical titles, same project | Flag the pair for a human. **Never auto-close** |
| 9 | Urgent inflation | more than ~5 issues at `priority 1` in one project | No write — report it. The tier has stopped meaning anything |

Checks 6, 8 and 9 are judgment, not defects. Report them in their own section, below the
mechanical ones, and never fold them into the batch confirmation.

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

- **One `save_issue` per issue**, carrying only the fields this groom is changing. Never
  attach a `patch` to a call that also moves `state` — see contract rule 2 in `linear.md`.
- **Read the response back** and compare each changed field to what was asked. Contract
  rule 3: an unconfirmed write is a failed write.
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

The same loop, narrowed: issues with `statusType: triage`, plus anything missing both
priority and project. Per issue propose a priority tier, a project, and a milestone if the
project has them — that is a *placement*, so the reasoning in `place` applies. An issue that
cannot be placed stays in triage with a note saying what is missing; parking it is a real
outcome, not a failure.
