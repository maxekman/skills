# Linear (MCP) — verified surface, priority, and the write contract

The argument lists below were taken from observed calls against `linear-server`, not from the
published schema. Where something is marked *never observed*, treat it as unavailable and say
so rather than trying it and narrating a guess about what happened.

## `save_issue`

Upsert — omit `id` to create, pass `id` to update.

| Group | Arguments |
|---|---|
| Identity | `id`, `title`, `description`, `patch` |
| Placement | `priority`, `team`, `project`, `milestone`, `parentId` |
| Classification | `labels` (replaces), `addLabels` (adds), `assignee`, `state` |
| Relations | `relatedTo`, `blockedBy`, `blocks`, `removeBlocks`, `removeBlockedBy`, `duplicateOf` |
| Misc | `links` |

**Never observed: `sortOrder`, `position`, `boardOrder`, `estimate`, `cycle`, `dueDate`.**
The first three are why the rank contract exists. The last three are readable via
`list_issues` `fields` but not settable here — if the user wants an estimate or a cycle set,
say it has to be done in the Linear UI.

`patch` takes a list of `replace` / `prepend` / `append` ops rather than resending a long
description. A `replace` whose `old_string` does not match **fails the entire call** — see
contract rule 2.

## `list_issues`

Arguments: `query`, `state`, `project`, `team`, `parentId`, `createdAt`, `includeArchived`,
`orderBy`, `limit`, `fields`.

`query` is **free-text semantic search**, not a filter language. Filter with the structured
arguments instead — `state`, `project`, `team`, `parentId` — and reach for `query` only when
looking for issues *about* something.

`fields` is a strict enum; an unknown value fails the call. Valid values:

```
id uuid title description projectMilestone priority estimate url gitBranchName
createdAt updatedAt archivedAt completedAt startedAt canceledAt dueDate
slaStartedAt slaMediumRiskAt slaHighRiskAt slaBreachesAt slaType
status statusType labels triageIntel createdBy createdById
assignee assigneeId delegate delegateId project projectId parentId team teamId cycleId
```

Ask for the narrow set you need. A backlog read for ranking wants
`id, title, status, statusType, priority, projectMilestone, assignee, createdAt, updatedAt`.

## `status` vs `statusType` — branch on the type

`status` is the team's own name for a workflow state. It is **not portable**: one team's
"In Progress" is another's "Doing", and a third has "Ready for review" where you expect
"In Review". Logic keyed to those strings works until it silently doesn't.

`statusType` is Linear's fixed category, and it is the one to branch on:

| `statusType` | Means | Typical names |
|---|---|---|
| `triage` | Not yet accepted | Triage |
| `backlog` | Accepted, not scheduled | Backlog, Icebox |
| `unstarted` | Scheduled, not begun | Todo, Ready |
| `started` | In flight | In Progress, Doing, In Review |
| `completed` | Done | Done, Shipped |
| `canceled` | Abandoned | Canceled, Duplicate |

**Compute on `statusType`, display `status`.** "Is this finished?" is
`statusType in (completed, canceled)` — never `status == "Done"`.

## Other tools

| Action | Tool | Arguments |
|---|---|---|
| Get issue | `get_issue` | `id` (human ID like `ACME-407`, uppercased), `includeRelations` |
| Workflow states | `list_issue_statuses` | team |
| Labels | `list_issue_labels` | `team`, `limit`, `name`, `includeGroups` |
| Projects | `list_projects` | `query`, `fields`, `limit` |
| Project detail | `get_project` | `query`, `includeResources`, `includeMilestones` |
| Milestones | `save_milestone` | `project`, `name`, `description` |
| Comments | `list_comments` / `save_comment` | `issueId`, `body`, `limit` |
| Teams | `list_teams` | `limit` |
| Current user | `get_user` | — |

`list_issue_statuses`, `list_issue_labels` and `list_projects` are read-only lookups this
skill calls constantly — `list_issue_statuses` on every status write, per rule 1 below. Put
all three in `settings.json` `permissions.allow`, or they interrupt for approval on the
critical path. That prompt is exactly what tempts a caller into guessing a state name
instead of resolving it.

## Priority rubric

Numeric. Linear sorts `0` last despite it being the lowest number, because it means "unset".

| Value | Tier | Assign it when |
|---|---|---|
| `1` | Urgent | Broken in production, blocking other people, or a deadline inside the week |
| `2` | High | Committed to the current milestone or cycle; the plan slips without it |
| `3` | Medium | Real, agreed work with no date pressure — **the default for a new issue** |
| `4` | Low | Worth doing, nobody would notice if it waited a quarter |
| `0` | None | Not yet judged. Fine in triage, a defect anywhere else |

Two rules that keep the tiers meaningful:

- **Urgent is scarce.** If more than a handful of issues in a project are `1`, the tier has
  stopped carrying information — say so during a groom rather than adding another.
- **Never leave a created issue at `0`.** An issue with no priority sorts below everything
  and is the one that resurfaces months later in an arbitrary place. Pick a tier, and say
  which one you picked and why.

## The write contract

Four rules. All four exist because each one has already failed in practice.

**1. Resolve the state before writing it.** Call `list_issue_statuses` for the team and match
the requested state against the real list — on `statusType` first, then name. No match means
stop and report the available states; it does not mean send the guess anyway. Guessed names
are the single largest cause of a status change that never happened.

**2. Never bundle `patch` with `state`.** `save_issue` is atomic: a `replace` op whose
`old_string` no longer matches returns *"Patch failed, nothing was saved"* and **the state
change dies with it**. Send them as two calls — patch first, state second — so a stale patch
can never swallow a status move.

The same applies to any risky field travelling with a status change. A status write should be
the smallest call you can make: `id` and `state`, nothing else.

**3. Read the status back.** `save_issue` returns the saved issue, `status` field included —
verification costs no extra call. Compare it to what was asked:

- Matches → report the change.
- Differs, or the response has no `status` → **the write failed.** Say so, name the issue,
  and show what the response actually said. Never narrate a status change you did not confirm.
- Response is an `{"error": ...}` object or an `Error:` string → also a failure, however
  plausible the surrounding text looks.

**4. Mind the preconditions.** Some states reject a bare write:

- `Duplicate` → returns HTTP 400 *"Issues can only be moved to a duplicate state when a
  duplicate issue relation exists"* unless `duplicateOf` was set in an **earlier** call.
  Set the relation, confirm it, then move the state.
- Removing a relation can fail on its own (`Error: Failed to remove 1 relation(s)`) while the
  rest of the call succeeds — check relations back explicitly when you changed them.
